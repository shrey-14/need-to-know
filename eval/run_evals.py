# Ragas runner: runs every eval_dataset.jsonl row through the real chat chain,
# checks RBAC/refusal behavior deterministically, scores answerable rows with
# Ragas, and saves one self-describing results file per run (manifest + summary +
# ops + failures + per-row scores). Exits non-zero on any hard-gate failure or
# unscored row. Eval phase.
import hashlib
import inspect
import json
import math
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

os.environ["LANGCHAIN_PROJECT"] = "rag-chatbot-rbac-evals"   # before app imports; load_dotenv won't override it

import psycopg
from langchain_groq import ChatGroq
from ragas import evaluate, EvaluationDataset, SingleTurnSample
from ragas.run_config import RunConfig
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness

from app.core.config import get_settings
from app.core.roles import allowed_categories
from app.ingestion.chunking import chunk_overlap, chunk_size
from app.monitoring.cost_tracker import ensure_table
from app.rag.chain import answer_question
from app.rag.retriever import RETRIEVAL_STRATEGY, get_relevant_documents, hf, vectorstore

EVAL_DIR = Path(__file__).parent
PROJECT_ROOT = EVAL_DIR.parent
DATASET_PATH = EVAL_DIR / "eval_dataset.jsonl"
RESULTS_DIR = EVAL_DIR / "results"
settings = get_settings()
JUDGE_MODEL = settings.groq_small_model


def is_decline(answer: str) -> bool:
    return "i don't have" in answer.lower()


def git_state() -> dict:
    def git(*args: str) -> str | None:
        try:
            return subprocess.run(
                ["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    return {
        "commit": git("rev-parse", "HEAD"),  # None until the repo has a first commit
        # Only modified tracked files count: untracked files (e.g. the previous
        # run's results JSON) don't change what the code does.
        "dirty": bool(git("status", "--porcelain", "--untracked-files=no")),
    }


def build_manifest(run_id: str, dataset_bytes: bytes, n_rows: int) -> dict:
    return {
        "run_id": run_id,
        "git": git_state(),
        "config": {
            "retrieval_strategy": RETRIEVAL_STRATEGY,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "retriever_k": inspect.signature(get_relevant_documents).parameters["k"].default,
            "embedding_model": settings.embedding_model,
            "answer_model": settings.groq_model,
            "judge_model": JUDGE_MODEL,
        },
        # chunk_size above is read from the code; this is read from the index.
        # If you change chunk_size but this count doesn't move, you forgot to
        # rebuild the index and the run measured the old chunks.
        "index_chunk_count": vectorstore._collection.count(),
        "dataset": {
            "path": str(DATASET_PATH.relative_to(PROJECT_ROOT)),
            "sha256": hashlib.sha256(dataset_bytes).hexdigest(),
            "rows": n_rows,
        },
    }


def nan_to_none(obj):
    """Recursively replace float NaN (unscored metrics) with None, so the file
    is valid JSON with `null`s."""
    if isinstance(obj, dict):
        return {k: nan_to_none(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [nan_to_none(v) for v in obj]
    if isinstance(obj, float) and math.isnan(obj):
        return None
    return obj


def db_now(conn) -> datetime:
    return conn.execute("SELECT now()").fetchone()[0]


def ops_summary(conn, started_at: datetime, ended_at: datetime) -> dict:
    """Aggregate this run's cost_log rows by the run's time window (DB clock).
    Only requests that reached the LLM write a row; refusals and out-of-scope
    short-circuits don't. Judge calls never go through log_cost, so this is the
    system's own cost/latency, not the evaluation's."""
    n, prompt, completion, cost, avg_ms, p95_ms = conn.execute(
        """
        SELECT count(*),
               COALESCE(sum(prompt_tokens), 0),
               COALESCE(sum(completion_tokens), 0),
               COALESCE(sum(estimated_cost), 0),
               avg(latency_ms),
               percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)
        FROM cost_log
        WHERE timestamp >= %s AND timestamp <= %s
        """,
        (started_at, ended_at),
    ).fetchone()
    return {
        "window": [started_at.isoformat(), ended_at.isoformat()],
        "llm_requests": n,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_cost_usd": float(cost),
        "cost_per_request_usd": float(cost) / n if n else None,
        "avg_latency_ms": round(float(avg_ms)) if avg_ms is not None else None,
        "p95_latency_ms": round(float(p95_ms)) if p95_ms is not None else None,
    }


def main() -> int:
    RESULTS_DIR.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    dataset_bytes = DATASET_PATH.read_bytes()
    rows = [json.loads(line) for line in dataset_bytes.decode().splitlines() if line.strip()]
    manifest = build_manifest(run_id, dataset_bytes, len(rows))

    ensure_table()   # eval never goes through main.py, so migrate the cost_log schema here too
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        started_at = db_now(conn)

    failures = []   # Layer B hard-gate failures
    samples, sample_rows = [], []

    for row in rows:
        result = answer_question(row["question"], row["role"])

        # Layer B: RBAC leak check — applies to EVERY row
        allowed = allowed_categories(row["role"])
        leaked = [c["category"] for c in result["contexts"] if c["category"] not in allowed]
        if leaked:
            failures.append({"id": row["id"], "check": "rbac_leak", "detail": sorted(set(leaked))})

        # Layer B: refusal/scope behavior
        if row["expected_behavior"] in ("refuse", "out_of_scope") and not is_decline(result["answer"]):
            failures.append({"id": row["id"], "check": row["expected_behavior"], "detail": "got an answer"})

        # Layer A input: only answerable rows go to Ragas
        if row["expected_behavior"] == "answer":
            samples.append(SingleTurnSample(
                user_input=row["question"],
                response=result["answer"],
                retrieved_contexts=[c["text"] for c in result["contexts"]],
                reference=row["reference"],
            ))
            sample_rows.append(row)

    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        ended_at = db_now(conn)
        ops = ops_summary(conn, started_at, ended_at)

    judge = LangchainLLMWrapper(ChatGroq(model=JUDGE_MODEL, api_key=settings.groq_api_key, temperature=0, reasoning_effort="low"))
    ragas_result = evaluate(
        dataset=EvaluationDataset(samples=samples),
        metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness()],
        llm=judge,
        embeddings=LangchainEmbeddingsWrapper(hf),
        run_config=RunConfig(max_workers=1, timeout=180, max_retries=5),
    )
    df = ragas_result.to_pandas()
    df["tag"] = [r["tag"] for r in sample_rows]
    df["id"] = [r["id"] for r in sample_rows]

    metrics = [c for c in df.columns if df[c].dtype.kind in "fi"]
    per_tag = df.groupby("tag")[metrics].mean().round(3)
    per_tag.insert(0, "n", df.groupby("tag").size())
    nan_counts = {m: int(df[m].isna().sum()) for m in metrics}

    summary = {
        "overall": {m: round(float(df[m].mean()), 3) for m in metrics},
        "per_tag": per_tag.reset_index().to_dict(orient="records"),
        "unscored": nan_counts,
        "layer_b": {"rows_checked": len(rows), "failures": len(failures)},
    }

    out = {
        "manifest": manifest,
        "summary": summary,
        "ops": ops,
        "failures": failures,
        "results": df.to_dict(orient="records"),
    }
    out_path = RESULTS_DIR / f"{run_id}.json"
    # allow_nan=False: fail loudly rather than ever write bare NaN (invalid JSON)
    out_path.write_text(json.dumps(nan_to_none(out), indent=2, default=str, allow_nan=False))

    print(f"\nRun {run_id} · commit {manifest['git']['commit'] or 'none'}"
          f"{' (dirty)' if manifest['git']['dirty'] else ''} · {manifest['config']}")
    print(per_tag.to_string())
    print(f"\nLayer B: {len(failures)} failure(s) across {len(rows)} rows")
    for f in failures:
        print("  FAIL:", f)
    print(f"Ops: {ops['llm_requests']} LLM requests · ${ops['total_cost_usd']:.6f} total · "
          f"avg {ops['avg_latency_ms']} ms · p95 {ops['p95_latency_ms']} ms")
    if any(nan_counts.values()):
        print(f"UNSCORED rows (judge failures — rescore before trusting averages): {nan_counts}")
    print(f"Saved {out_path.relative_to(PROJECT_ROOT)}")

    return 1 if failures or any(nan_counts.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
