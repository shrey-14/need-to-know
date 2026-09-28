# Eval runner: runs every eval_dataset.jsonl row through the real chat chain and
# saves one self-describing results file per run (manifest + summary + ops +
# failures + per-row results). Eval phase.
#
#   Layer B (always): RBAC-leak and refusal/out-of-scope checks — hard gates.
#   Tier 2  (always): must_contain facts in each answer -> PASS / PARTIAL / FAIL.
#                     Deterministic, no judge LLM, so it fits the free tier.
#   Ragas   (--ragas): LLM-judged metrics. Expensive; use at milestones only.
#
#   venv/bin/python -m eval.run_evals            # Layer B + Tier 2
#   venv/bin/python -m eval.run_evals --ragas    # ... plus Ragas
#
# Exits non-zero on any Layer B failure, or (with --ragas) any unscored row.
# Tier 2 misses are quality results, not gates, so they don't fail the run.
import argparse
import hashlib
import inspect
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

os.environ["LANGCHAIN_PROJECT"] = "rag-chatbot-rbac-evals"   # before app imports; load_dotenv won't override it

import pandas as pd
import psycopg

from app.core.config import get_settings
from app.core.roles import allowed_categories
from app.ingestion.chunking import chunk_overlap, chunk_size
from app.monitoring.cost_tracker import ensure_table
from app.rag.chain import answer_question
from app.rag.retriever import RETRIEVAL_STRATEGY, get_relevant_documents, vectorstore

from eval.checks import git_state, must_contain_hits

EVAL_DIR = Path(__file__).parent
PROJECT_ROOT = EVAL_DIR.parent
DATASET_PATH = EVAL_DIR / "eval_dataset.jsonl"
RESULTS_DIR = EVAL_DIR / "results"
settings = get_settings()
JUDGE_MODEL = settings.groq_small_model


def is_decline(answer: str) -> bool:
    return "i don't have" in answer.lower()


def build_manifest(run_id: str, dataset_bytes: bytes, n_rows: int, use_ragas: bool) -> dict:
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
            "judge_model": JUDGE_MODEL if use_ragas else None,   # None = no LLM judge ran
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


def grade(row: dict, answer: str) -> dict:
    """Tier 2: which of the row's must_contain facts appear in the answer."""
    hits = must_contain_hits(row["must_contain"], answer)
    if all(hits):
        verdict = "PASS"
    elif any(hits):
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"
    return {
        "verdict": verdict,
        "score": sum(hits) / len(hits),
        "missing": [m for m, h in zip(row["must_contain"], hits) if not h],
        # A refusal is a FAIL either way; flagging it separately tells a retrieval
        # miss ("I don't have that") apart from a wrong answer ("4 employees").
        "refused": is_decline(answer),
    }


def tier2_per_tag(graded: pd.DataFrame) -> pd.DataFrame:
    per_tag = graded.groupby("tag").agg(
        n=("id", "size"),
        pass_=("verdict", lambda v: int((v == "PASS").sum())),
        partial=("verdict", lambda v: int((v == "PARTIAL").sum())),
        fail=("verdict", lambda v: int((v == "FAIL").sum())),
        refused=("refused", "sum"),
        pass_rate=("verdict", lambda v: (v == "PASS").mean()),
        mean_score=("score", "mean"),
    ).round(3)
    return per_tag.rename(columns={"pass_": "pass"})


def run_ragas(samples: list[dict]) -> pd.DataFrame:
    """LLM-judged metrics, keyed by row id. Imported lazily so Tier 2-only runs
    don't need ragas (or its judge quota) at all."""
    from langchain_groq import ChatGroq
    from ragas import EvaluationDataset, SingleTurnSample, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import FactualCorrectness, Faithfulness, LLMContextRecall
    from ragas.run_config import RunConfig

    from app.rag.retriever import hf

    judge = LangchainLLMWrapper(ChatGroq(model=JUDGE_MODEL, api_key=settings.groq_api_key, temperature=0, reasoning_effort="low"))
    result = evaluate(
        dataset=EvaluationDataset(samples=[
            SingleTurnSample(
                user_input=s["question"],
                response=s["answer"],
                retrieved_contexts=s["contexts"],
                reference=s["reference"],
            )
            for s in samples
        ]),
        metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness()],
        llm=judge,
        embeddings=LangchainEmbeddingsWrapper(hf),
        run_config=RunConfig(max_workers=1, timeout=180, max_retries=5),
    )
    df = result.to_pandas()
    metrics = [c for c in df.columns if df[c].dtype.kind in "fi"]
    df = df[metrics]
    df.insert(0, "id", [s["id"] for s in samples])
    return df


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--ragas", action="store_true", help="also run LLM-judged Ragas metrics")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    dataset_bytes = DATASET_PATH.read_bytes()
    rows = [json.loads(line) for line in dataset_bytes.decode().splitlines() if line.strip()]
    manifest = build_manifest(run_id, dataset_bytes, len(rows), args.ragas)

    ensure_table()   # eval never goes through main.py, so migrate the cost_log schema here too
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        started_at = db_now(conn)

    failures = []   # Layer B hard-gate failures
    answered = []   # one record per answer row: its answer, Tier 2 grade, and what Ragas needs

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

        if row["expected_behavior"] == "answer":
            answered.append({
                "id": row["id"],
                "tag": row["tag"],
                "question": row["question"],
                "reference": row["reference"],
                "answer": result["answer"],
                "sources": result["sources"],
                "contexts": [c["text"] for c in result["contexts"]],
                **grade(row, result["answer"]),   # Tier 2
            })

    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        ended_at = db_now(conn)
        ops = ops_summary(conn, started_at, ended_at)

    graded = pd.DataFrame(answered)
    t2_per_tag = tier2_per_tag(graded)
    summary = {
        "tier2": {
            "overall": {
                "n": len(graded),
                "pass": int((graded["verdict"] == "PASS").sum()),
                "partial": int((graded["verdict"] == "PARTIAL").sum()),
                "fail": int((graded["verdict"] == "FAIL").sum()),
                "refused": int(graded["refused"].sum()),
                "pass_rate": round(float((graded["verdict"] == "PASS").mean()), 3),
                "mean_score": round(float(graded["score"].mean()), 3),
            },
            "per_tag": t2_per_tag.reset_index().to_dict(orient="records"),
        },
        "layer_b": {"rows_checked": len(rows), "failures": len(failures)},
    }

    nan_counts = {}
    ragas_per_tag = None
    results = graded
    if args.ragas:
        ragas_df = run_ragas(answered)
        metrics = [c for c in ragas_df.columns if c != "id"]
        results = graded.merge(ragas_df, on="id", how="left")
        ragas_per_tag = results.groupby("tag")[metrics].mean().round(3)
        ragas_per_tag.insert(0, "n", results.groupby("tag").size())
        nan_counts = {m: int(results[m].isna().sum()) for m in metrics}
        summary["ragas"] = {
            "overall": {m: round(float(results[m].mean()), 3) for m in metrics},
            "per_tag": ragas_per_tag.reset_index().to_dict(orient="records"),
            "unscored": nan_counts,
        }

    out = {
        "manifest": manifest,
        "summary": summary,
        "ops": ops,
        "failures": failures,
        "results": results.to_dict(orient="records"),
    }
    out_path = RESULTS_DIR / f"{run_id}.json"
    # allow_nan=False: fail loudly rather than ever write bare NaN (invalid JSON)
    out_path.write_text(json.dumps(nan_to_none(out), indent=2, default=str, allow_nan=False))

    print(f"\nRun {run_id} · commit {(manifest['git']['commit'] or 'none')[:7]}"
          f"{' (dirty)' if manifest['git']['dirty'] else ''} · {manifest['config']}")
    t2 = summary["tier2"]["overall"]
    print(f"\nTier 2 (must_contain): {t2['pass']} PASS · {t2['partial']} PARTIAL · {t2['fail']} FAIL"
          f" ({t2['refused']} refused) of {t2['n']} · pass_rate {t2['pass_rate']} · mean_score {t2['mean_score']}")
    print(t2_per_tag.to_string())
    for r in answered:
        if r["verdict"] != "PASS":
            why = "refused" if r["verdict"] == "FAIL" and r["refused"] else f"missing {r['missing']}"
            if r["verdict"] == "PARTIAL" and r["refused"]:
                why += " (declined the rest)"
            print(f"  {r['verdict']:7} {r['id']:9} {why}")
    if ragas_per_tag is not None:
        print("\nRagas:")
        print(ragas_per_tag.to_string())
        if any(nan_counts.values()):
            print(f"UNSCORED rows (judge failures — rescore before trusting averages): {nan_counts}")
    print(f"\nLayer B: {len(failures)} failure(s) across {len(rows)} rows")
    for f in failures:
        print("  FAIL:", f)
    print(f"Ops: {ops['llm_requests']} LLM requests · ${ops['total_cost_usd']:.6f} total · "
          f"avg {ops['avg_latency_ms']} ms · p95 {ops['p95_latency_ms']} ms")
    print(f"Saved {out_path.relative_to(PROJECT_ROOT)}")

    return 1 if failures or any(nan_counts.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
