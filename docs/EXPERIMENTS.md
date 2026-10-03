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
| Commit | `8992c52` + uncommitted eval-harness changes (**dirty**), since committed as `745d963`. See the note below. |
| Results | Tier 1: `eval/results/retrieval-20260928-223035.json` · Tier 2: `eval/results/20260928-223536.json` (+ repeat `20260928-222308.json`) |
| Dataset | sha256 `9537e4eb…a5dd0ba`: 30 rows (24 answer, 4 refuse, 2 out_of_scope) |
| Compared against | — |

> **Dirty-run note:** all three runs are marked `dirty`. The uncommitted changes were the eval harness itself (`eval/checks.py`, `eval/retrieval_check.py`, `eval/run_evals.py`, the dataset's new `evidence`/`must_contain` fields) and an unused `qwen_model` setting in `app/core/config.py`. None of them touch the answering pipeline under test, so the numbers stand.

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

---

## EXP-001 — Larger chunks (250/30 → 800/150)

| | |
|---|---|
| Date | 2026-10-03 |
| Commit | `34a882b` |
| Results | Tier 1: `eval/results/retrieval-20261003-133510.json` (k=5) · `retrieval-20261003-132554.json` (k=15, exploratory) · Tier 2: `eval/results/20261003-132828.json` |
| Dataset | sha256 `9537e4eb…a5dd0ba` (same as EXP-000) |
| Compared against | EXP-000 |

**Hypothesis / prediction:** not written down before the run. The working expectation from the EXP-000 analysis was:
- 250-character chunks separate figures from their labels (sf-02's "Net Income: $275 million" chunk doesn't contain "Q2").
- Larger chunks should therefore recover sf-02, sf-04, mc-02 and the multi_doc rows.
- entity_typo should stay at 1.0.
- Overall evidence recall should rise above 0.70.

**Change:**
- `app/ingestion/chunking.py`: `chunk_size` 250 → 800, `chunk_overlap` 30 → 150.
- `app/ingestion/build_index.py`: the collection is now deleted before re-indexing. Without this, re-chunking left stale chunks in place. The index went from 603 to **334 chunks**, and `--validate` reports 0 unreachable evidence items.
- Everything else is unchanged: dense retrieval, k=5, same models.

> **Discarded run:** `20261003-130409.json` was run before the `build_index` fix. Its index still reported 603 chunks: 128 new large chunks mixed with about 375 stale 250-character ones. It isn't cited here.

> **Tier 1 k=5 run** is marked `dirty` only because a tracked results JSON (the discarded run) was deleted. No code differed from `34a882b`. Tier 2 is clean (`dirty: false`).

**Results** (k=5):

| Tag | n (T1/T2) | Evidence recall | Δ | Pass rate | Δ | Mean score (T2) | Δ |
|---|---|---|---|---|---|---|---|
| single_fact | 11/11 | 0.636 | +0.045 | 0.545 | 0 | 0.591 | 0 |
| aggregate | 1/5 | 0.250 | 0 | 0.000 | 0 | 0.050 | 0 |
| multi_doc | 3/3 | 0.417 | +0.139 | 0.000 | 0 | 0.367 | +0.067 |
| multi_chunk | 2/2 | 0.500 | +0.167 | 0.500 | +0.500 | 0.500 | +0.143 |
| entity_typo | 3/3 | 1.000 | 0 | 0.667 | 0 | 0.667 | 0 |
| **overall** | 20/24 | **0.625** | **+0.063** | **0.375** | **+0.042** | 0.452 | +0.020 |

Tier 2 overall: 9 PASS / 4 PARTIAL / 11 FAIL (10 refused), against 8 / 5 / 11 (10 refused) in EXP-000.

**Rows that flipped:**

| Row | Tier 1 evidence recall | Tier 2 verdict | Note |
|---|---|---|---|
| sf-04 | 0 → 1.0 | FAIL → **PASS** | The "Q3" label and the "$2 million" figure now share a chunk, as predicted. |
| mc-01 | 0.67 → 1.0 | PARTIAL → **PASS** | The full leave table now arrives intact. |
| sf-07 | 0.5 → 1.0 | PARTIAL → PARTIAL | Retrieval is complete now, but the answer still omits "bi-weekly". This is a generation issue, not retrieval. |
| multi-01 | 0.33 → 0.5 | PARTIAL (0.4 → 0.6) | 3 of 5 budget lines, up from 2. |
| multi-02 | 0 → 0.25 | FAIL → FAIL | One quarter retrieved; the model still refuses. |
| **sf-03** | **1.0 → 0** | **PASS → FAIL** | **Regression.** The 2024 CAC chunk is now outranked by the four quarterly reports' "targets" chunks, which all discuss customer acquisition. The CAC line is diluted inside a larger chunk. |

**Layer B:** 0 failures / 30 rows.

**Ops:**

| | EXP-000 | EXP-001 | Δ |
|---|---|---|---|
| Prompt tokens per run | 17,828 | 22,599 | +27% |
| Cost per request | $0.000173 | $0.000207 | +20% |
| Total cost per run | $0.004857 | $0.005806 | +20% |
| Avg / p95 latency | 2196 / 6446 ms | 3775 / 9221 ms | +1.6 s / +2.8 s |

The latency increase is partly noise: EXP-000's repeat run averaged 3122 ms. The token increase is real and expected, since each of the 5 chunks is larger.

**Observations:**
- **Larger chunks bring the right evidence closer to the top, but not into the top 5.** At k=15, evidence recall is **0.838** (0.692 at 250/30). sf-02, sf-06, multi-02 and mc-02 have their evidence in ranks 6–15 but miss the top 5. So the relevant chunk is now *retrieved* but *ranked too low*, which is exactly what a reranker over a wider candidate pool fixes.
- **sf-11 (compliance frameworks) is missing even at k=15.** That fits an exact-term problem (DPDP, GDPR, PCI-DSS), so hybrid BM25 is the likely fix.
- **Bigger chunks dilute specific facts (sf-03).** A one-line KPI inside an 800-character chunk competes with chunks that are entirely about the same topic. Hybrid search would also help here, since "Customer Acquisition Cost" is an exact phrase.
- **The net Tier 2 gain is small:** +1 row (2 gained, 1 lost), and the row-level noise floor is about 1 row. Tier 1 shows a clearer gain (+0.063 at k=5, +0.146 at k=15).
- Aggregates are unchanged, as expected; chunking can't count rows.

**Decision:** **keep 800/150** as the chunking for the following experiments:
- Retrieval improved at both k values, multi_chunk improved, and the one regression has an identified cause that the next experiments target.
- Next: **EXP-002 hybrid BM25 + RRF**, targeting sf-02, sf-03, sf-06 and sf-11.
- Then **EXP-003 reranker** over a k≈15–20 hybrid pool, targeting the rank 6–15 evidence.
