# Tier 1 eval: retrieval-only, no LLM calls. For each answerable row, calls
# get_relevant_documents(question, role) and checks which of the row's evidence
# strings appear in the retrieved chunks. Deterministic and free, so one run is
# enough, and it can be re-run on every chunking/k/retrieval change. Eval phase.
#
#   venv/bin/python -m eval.retrieval_check              # score at the default k
#   venv/bin/python -m eval.retrieval_check --k 8        # try a different k (no code change)
#   venv/bin/python -m eval.retrieval_check --validate   # is every evidence string in the index at all?
import argparse
import hashlib
import inspect
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.core.config import get_settings
from app.core.roles import allowed_categories
from app.ingestion.chunking import chunk_overlap, chunk_size
from app.rag.retriever import RETRIEVAL_STRATEGY, get_relevant_documents, vectorstore
from eval.checks import evidence_hits, git_state

EVAL_DIR = Path(__file__).parent
PROJECT_ROOT = EVAL_DIR.parent
DATASET_PATH = EVAL_DIR / "eval_dataset.jsonl"
RESULTS_DIR = EVAL_DIR / "results"
DEFAULT_K = inspect.signature(get_relevant_documents).parameters["k"].default
settings = get_settings()


def validate(rows: list[dict]) -> int:
    """Every evidence item must exist in some chunk the row's role can read.
    A miss means the item can never be retrieved: a typo in the dataset, or the
    text got split across a chunk boundary after a chunking change."""
    data = vectorstore._collection.get(include=["documents", "metadatas"])
    all_chunks = [{"text": t, "source": m["source"], "category": m["category"]}
                  for t, m in zip(data["documents"], data["metadatas"])]
    bad = 0
    for row in rows:
        allowed = allowed_categories(row["role"])
        chunks = [c for c in all_chunks if c["category"] in allowed]
        for item, hit in zip(row["evidence"], evidence_hits(row["evidence"], chunks)):
            if not hit:
                bad += 1
                print(f"  NOT IN INDEX  {row['id']}: {item}")
    print(f"{bad} unreachable evidence item(s) across {len(rows)} rows")
    return 1 if bad else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    dataset_bytes = DATASET_PATH.read_bytes()
    all_rows = [json.loads(line) for line in dataset_bytes.decode().splitlines() if line.strip()]
    # Rows with no evidence (refusals, and aggregates that top-k can't answer) aren't retrieval-checkable.
    rows = [r for r in all_rows if r.get("evidence")]
    skipped = [r["id"] for r in all_rows if r["expected_behavior"] == "answer" and not r.get("evidence")]

    if args.validate:
        return validate(rows)

    records = []
    for row in rows:
        docs = get_relevant_documents(row["question"], row["role"], k=args.k)
        chunks = [{"text": d.page_content, "source": d.metadata["source"]} for d in docs]
        hits = evidence_hits(row["evidence"], chunks)
        records.append({
            "id": row["id"],
            "tag": row["tag"],
            "evidence_recall": sum(hits) / len(hits),
            "complete": all(hits),
            "missing": [e for e, h in zip(row["evidence"], hits) if not h],
            "retrieved_sources": [Path(c["source"]).name for c in chunks],
        })

    df = pd.DataFrame(records)
    per_tag = df.groupby("tag").agg(
        n=("id", "size"),
        evidence_recall=("evidence_recall", "mean"),
        complete=("complete", "mean"),
    ).round(3)

    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = {
        "manifest": {
            "run_id": run_id,
            "kind": "retrieval_check",
            "git": git_state(),
            "config": {
                "retrieval_strategy": RETRIEVAL_STRATEGY,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "retriever_k": args.k,
                "embedding_model": settings.embedding_model,
            },
            "index_chunk_count": vectorstore._collection.count(),
            "dataset": {
                "path": str(DATASET_PATH.relative_to(PROJECT_ROOT)),
                "sha256": hashlib.sha256(dataset_bytes).hexdigest(),
                "rows_checked": len(rows),
                "rows_skipped_no_evidence": skipped,
            },
        },
        "summary": {
            "overall": {
                "evidence_recall": round(float(df["evidence_recall"].mean()), 3),
                "complete": round(float(df["complete"].mean()), 3),
            },
            "per_tag": per_tag.reset_index().to_dict(orient="records"),
        },
        "results": records,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"retrieval-{run_id}.json"
    out_path.write_text(json.dumps(out, indent=2, allow_nan=False))

    cfg = out["manifest"]["config"]
    print(f"\nRetrieval check · {cfg['retrieval_strategy']} · chunk {cfg['chunk_size']}/{cfg['chunk_overlap']}"
          f" · k={cfg['retriever_k']} · commit {(out['manifest']['git']['commit'] or 'none')[:7]}"
          f"{' (dirty)' if out['manifest']['git']['dirty'] else ''}")
    print(per_tag.to_string())
    print(f"\noverall evidence_recall={out['summary']['overall']['evidence_recall']}"
          f"  complete={out['summary']['overall']['complete']}  (n={len(df)})")
    print(f"skipped (no evidence): {', '.join(skipped)}")
    for r in records:
        if r["missing"]:
            print(f"  MISS {r['id']:9} missing {r['missing']}")
    print(f"Saved {out_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
