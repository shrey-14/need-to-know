# Retrieval Experiments Log

Every structural or architectural change to the RAG pipeline (chunking, k, retrieval strategy, reranking, prompt, model) gets one entry here. Each entry is measured against `eval/eval_dataset.jsonl` with `eval/run_evals.py`, and each one names the results file it came from.

## Protocol

1. **Commit before you run.** The manifest records the git commit plus a `dirty` flag. A run from a dirty tree can't be reproduced, so don't cite it as the result of an experiment.
2. **Rebuild the index after any ingestion change** (chunk size or overlap, loaders, metadata) with `uv run python -m app.ingestion.build_index`. Then check that `manifest.index_chunk_count` changed. If it didn't, the run measured the old chunks.
3. **Write the prediction before running.** Say which tags should move, which way, and why. A prediction that turns out wrong is still a finding.
4. **Run twice.** The judge and answer models are non-deterministic. If two runs of the same commit differ by *x* on a metric, a change smaller than *x* is noise.
5. **Check `summary.unscored` first.** If any row is unscored (NaN, meaning the judge was rate-limited or timed out), rescore it before you trust the averages. `run_evals.py` exits non-zero in that case.
6. **Change one thing per experiment.** If two changes have to ship together, say so, and don't attribute the result to either one alone.
7. **Keep the dataset fixed within a comparison.** If `manifest.dataset.sha256` differs between two runs, they aren't comparable. Re-run the baseline on the new dataset first.

**Headline metrics:** context recall (did retrieval find the evidence?), factual correctness (is the answer right?), and Layer B failures (must be 0).

Faithfulness is reported but isn't a headline metric, because it scores 1.0 on refusals. Always read an average alongside its per-tag `n`. Some tags have only 2–3 rows, so a single row moves the average by 0.33–0.5.

**Ops numbers** come from Supabase `cost_log`, over the run's time window. Two caveats:
- Only requests that reach the answer LLM are logged. Refusals, out-of-scope short-circuits, and scope-classifier calls aren't.
- Other traffic hitting the same database during a run would be counted too, so don't run evals while using the app.

---

## Entry template

```markdown
## EXP-NNN — <short name>

| | |
|---|---|
| Date | YYYY-MM-DD |
| Commit | `abc1234` |
| Results | `eval/results/<run_id>.json` (+ repeat: `<run_id>.json`) |
| Compared against | EXP-NNN |

**Hypothesis / prediction** (written before running):
<what should change, on which tags, and why>

**Change:**
<exactly what was changed — config diff, files touched>

**Results** (per tag; values from `summary.per_tag`):

| Tag | n | Context recall | Δ | Factual correctness | Δ |
|---|---|---|---|---|---|
| single_fact | | | | | |
| aggregate | | | | | |
| multi_doc | | | | | |
| multi_chunk | | | | | |
| entity_typo | | | | | |
| **overall** | | | | | |

**Layer B:** <n> failures / <rows> rows — <ids if any>
**Unscored rows:** <none / list>
**Ops:** <n> LLM requests · $<total> · avg <ms> ms · p95 <ms> ms

**Observations:**
<what actually moved; which specific rows flipped and why>

**Decision:** keep / revert / follow up with EXP-NNN
```

---

## EXP-000 — Baseline

| | |
|---|---|
| Date | |
| Commit | *(make the first commit, then fill this in)* |
| Results | |
| Compared against | — |

**Config** (from the manifest):

| Setting | Value |
|---|---|
| Retrieval strategy | dense (Chroma similarity search with a role `category` `$in` filter) |
| Chunking | MarkdownHeaderTextSplitter → RecursiveCharacterTextSplitter, `chunk_size=250`, `chunk_overlap=30`; HR CSV is one document per row |
| k | 5 |
| Embeddings | `BAAI/bge-base-en-v1.5` (normalized) |
| Answer model | `openai/gpt-oss-120b` (Groq) |
| Judge model | `openai/gpt-oss-120b` (Groq, temperature 0) |
| Dataset | 30 rows: 24 answer, 4 refuse, 2 out_of_scope |

**Noise floor:** run 1 vs run 2, max |Δ| per metric =

**Results:**

| Tag | n | Context recall | Factual correctness |
|---|---|---|---|
| single_fact | 11 | | |
| aggregate | 5 | | |
| multi_doc | 3 | | |
| multi_chunk | 2 | | |
| entity_typo | 3 | | |
| **overall** | 24 | | |

**Layer B:**
**Ops:**

**Observations:**

**Decision:**
