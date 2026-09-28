# Retrieval Experiments Log

Every structural or architectural change to the RAG pipeline (chunking, k, retrieval strategy, reranking, prompt, model) gets one entry here. Each entry is measured against `eval/eval_dataset.jsonl` and names the results files it came from.

## Eval tiers

| Tier | Command | What it measures | LLM calls | When |
|---|---|---|---|---|
| **1: Retrieval** | `venv/bin/python -m eval.retrieval_check` | **Evidence recall**: share of each row's `evidence` strings found in the top-k chunks | 0 | Every change |
| **2: Answers** | `venv/bin/python -m eval.run_evals` | **Pass rate**: share of rows whose answer contains all of its `must_contain` facts (PASS / PARTIAL / FAIL); plus Layer B | 28 (answering only) | Every change |
| **Layer B** | (part of Tier 2) | RBAC leaks, refusals and out-of-scope handling: hard gates, must be 0 | — | Every change |
| **3: Ragas** | `venv/bin/python -m eval.run_evals --ragas` | LLM-judged context recall, faithfulness and factual correctness | ~200 judge calls | Milestones only |

**Headline metrics:** Tier 1 evidence recall, Tier 2 pass rate, and Layer B failures (must be 0).

Ragas isn't a headline metric. A full run exceeds the Groq free-tier daily token limit, and the `gpt-oss-20b` judge produced obvious misgrades in testing (for example, faithfulness 0.0 on a correct, supported answer).

## Protocol

1. **Commit before you run.** The manifest records the git commit plus a `dirty` flag. A dirty run can't be reproduced from its commit hash, so don't cite it as an experiment's result.
2. **Rebuild the index after any ingestion change** (chunk size or overlap, loaders, metadata):
   - Rebuild with `venv/bin/python -m app.ingestion.build_index`.
   - Check that `manifest.index_chunk_count` changed. If it didn't, the run measured the old chunks.
   - Run `venv/bin/python -m eval.retrieval_check --validate`. A new chunk boundary can split an evidence string, which makes it impossible to retrieve. Fix the dataset first if anything is reported.
3. **Write the prediction before running.** Say which rows or tags should move, which way, and why. A prediction that turns out wrong is still a finding.
4. **Noise:**
   - Tier 1 is deterministic, so one run is enough.
   - Tier 2 depends on the answer LLM. Run it twice; if the two runs' pass rates differ by *x*, a change smaller than *x* is noise.
   - Ragas: always run it twice, and check `summary.ragas.unscored` is 0 before trusting any average.
5. **Change one thing per experiment.** If two changes have to ship together, say so, and don't attribute the result to either one alone.
6. **Keep the dataset fixed within a comparison.** Runs with different `manifest.dataset.sha256` values aren't comparable. Re-run the baseline on the new dataset first.
7. **Compare rows, not just averages.** Tags have 1–11 rows, so one row moves a tag's number by 0.09–1.0. Always record which rows flipped.

**Ops numbers** come from Supabase `cost_log`, over the run's time window. Caveats:
- Only requests that reach the answer LLM are logged. Refusals, out-of-scope short-circuits and scope-classifier calls aren't.
- Other traffic hitting the same database during a run is counted too, so don't use the app while evals run.
- Groq latency varies about ±1 s between identical runs, so latency differences smaller than that are noise.

---

## Entry template

```markdown
## EXP-NNN — <short name>

| | |
|---|---|
| Date | YYYY-MM-DD |
| Commit | `abc1234` |
| Results | Tier 1: `eval/results/retrieval-<id>.json` · Tier 2: `<id>.json` (+ repeat `<id>.json`) |
| Compared against | EXP-NNN |

**Hypothesis / prediction** (written before running):
<which rows/tags should move, which way, and why>

**Change:**
<exactly what changed: config diff, files touched>

**Results:**

| Tag | n (T1/T2) | Evidence recall | Δ | Pass rate | Δ |
|---|---|---|---|---|---|
| single_fact | 11/11 | | | | |
| aggregate | 1/5 | | | | |
| multi_doc | 3/3 | | | | |
| multi_chunk | 2/2 | | | | |
| entity_typo | 3/3 | | | | |
| **overall** | 20/24 | | | | |

**Rows that flipped:** <id: before → after>
**Layer B:** <n> failures / 30 rows
**Ops:** <n> LLM requests · $<total> · avg <ms> ms · p95 <ms> ms

**Observations:**
<what actually moved, and why>

**Decision:** keep / revert / follow up with EXP-NNN
```

---

## EXP-000 — Baseline

| | |
|---|---|
| Date | 2026-09-28 |
| Commit | `8992c52` + uncommitted eval-harness changes (**dirty**). See the note below. |
| Results | Tier 1: `eval/results/retrieval-20260928-223035.json` · Tier 2: `eval/results/20260928-223536.json` (+ repeat `20260928-222308.json`) |
| Dataset | sha256 `9537e4eb…a5dd0ba`: 30 rows (24 answer, 4 refuse, 2 out_of_scope) |
| Compared against | — |

> **Dirty-run note:** all three runs are marked `dirty`. The uncommitted changes were the eval harness itself (`eval/checks.py`, `eval/retrieval_check.py`, `eval/run_evals.py`, the dataset's new `evidence`/`must_contain` fields) and an unused `qwen_model` setting in `app/core/config.py`. None of them touch the answering pipeline under test, so the numbers stand. Replace the commit above with the hash of the commit that contains these files.

**Config** (from the manifest):

| Setting | Value |
|---|---|
| Retrieval strategy | dense (Chroma similarity search with a role `category` `$in` filter) |
| Chunking | MarkdownHeaderTextSplitter → RecursiveCharacterTextSplitter, `chunk_size=250`, `chunk_overlap=30`; HR CSV is one document per row |
| Index | 603 chunks |
| k | 5 |
| Embeddings | `BAAI/bge-base-en-v1.5` (normalized) |
| Answer model | `openai/gpt-oss-120b` (Groq) |
| Judge model | none (Tier 1 and 2 only) |

**Noise floor (Tier 2):** the two runs (`222308`, `223536`) gave **identical verdicts on all 24 rows**, so the measured noise is 0.000 on pass rate and mean score. With only two runs, treat a single row flipping in a future experiment as possible noise. Two or more rows moving the same way is a signal.

**Results:**

| Tag | n (T1/T2) | Evidence recall (T1) | Evidence complete (T1) | Pass rate (T2) | PASS / PARTIAL / FAIL | Refused | Mean score (T2) |
|---|---|---|---|---|---|---|---|
| single_fact | 11/11 | 0.591 | 0.545 | 0.545 | 6 / 1 / 4 | 4 | 0.591 |
| aggregate | 1/5 | 0.250 | 0.000 | 0.000 | 0 / 1 / 4 | 2 | 0.050 |
| multi_doc | 3/3 | 0.278 | 0.000 | 0.000 | 0 / 2 / 1 | 2 | 0.300 |
| multi_chunk | 2/2 | 0.333 | 0.000 | 0.000 | 0 / 1 / 1 | 1 | 0.357 |
| entity_typo | 3/3 | 1.000 | 1.000 | 0.667 | 2 / 0 / 1 | 1 | 0.667 |
| **overall** | 20/24 | **0.562** | 0.450 | **0.333** | 8 / 5 / 11 | 10 | 0.432 |

The Tier 1 aggregate row is agg-03 only. agg-01/02/04/05 have no evidence, because top-k retrieval can't surface a count over 100 rows.

**Layer B:** 0 failures / 30 rows (no RBAC leaks; all 4 refusals and 2 out-of-scope rows handled correctly).

**Ops:**

| Run | LLM requests | Total cost | Avg latency | p95 latency |
|---|---|---|---|---|
| 223536 | 28 | $0.004857 | 2196 ms | 6446 ms |
| 222308 (repeat) | 27 | $0.004919 | 3122 ms | 8175 ms |

That's about $0.00017 per request, with 17.8k prompt and 3.6k completion tokens per run.

**Failures by cause** (Tier 1 and Tier 2 agree on every retrieval miss):

| Cause | Rows | Evidence |
|---|---|---|
| **Retrieval miss → refusal** | sf-02, sf-04, sf-06, sf-11, multi-02, mc-02 | Evidence recall 0 at k=5, and the model correctly says "I don't have that information". |
| **Partial retrieval → partial answer** | sf-07, multi-01, multi-03, mc-01 | Only some evidence retrieved; the answer covers exactly what was retrieved (for example, multi-01 gives only the $7M Digital line of the $15M breakdown). |
| **Counting over top-k (confidently wrong)** | agg-02 ("4" vs 15), agg-05 ("four" vs 10), agg-03 (1 of 4 names) | The model counts the 5 retrieved rows. This is the most harmful failure: wrong, not refused. |
| **Aggregate refused** | agg-01, agg-04 | No evidence possible at any k. |
| **Name typo** | typo-02 ("Chaudhary" vs "Chowdhury") | Retrieval found both Isha Chowdhury rows, but the model declined, probably because of the name mismatch. |

**Observations:**
- **Raising k alone doesn't fix retrieval.** An exploratory Tier 1 sweep from the same dirty tree (result files not kept) gave:
  - Overall evidence recall **0.562 → 0.625 → 0.692** at k = 5 / 8 / 15.
  - Even at k=15, sf-02, sf-04 and sf-11 and all of multi-01/02/03 still miss.
  - The right chunks aren't in the top 15. This is a ranking problem: short chunks, with exact terms like "Net Income", "Q3" and "GDPR" diluted in the embedding. That points to larger chunks (EXP-001) and hybrid BM25 search (a later experiment).
- **Aggregates need a structural fix.** No retrieval setting can count 100 rows. A prompt rule against counting would at least turn the wrong answers into refusals.
- **Every refusal traced back to retrieval.** When the evidence was retrieved, the answer model used it correctly: no false refusals on found evidence, except typo-02.
- **The source data contradicts itself:** the 2024 marketing budget is $15M in `marketing_report_2024.md` but "$2.3 billion" in `quarterly_financial_report.md`, and the founding year is 2016 in the handbook but 2018 in the engineering doc. The references follow the role-visible source.

**Decision:** baseline for EXP-001 onward.
