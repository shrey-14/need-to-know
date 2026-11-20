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

---

## EXP-002 — Hybrid retrieval (BM25 + RRF), then contextual chunk headers

This experiment has **two stages, measured separately**, so each change's effect can be attributed:
- **Stage A:** hybrid retrieval.
- **Stage B:** contextual chunk headers, added on top of Stage A.

The final EXP-002 configuration is A + B.

### Stage A — Hybrid retrieval: dense + BM25, fused with RRF

| | |
|---|---|
| Date | 2026-10-05 |
| Commit | `28c75cf` + uncommitted hybrid retriever (**dirty**). See the note below. |
| Results | Tier 1: `eval/results/retrieval-20261005-112550.json` (k=5) · `retrieval-20261005-112615.json` (k=15) · Tier 2: `eval/results/20261005-112707.json` |
| Dataset | sha256 `9537e4eb…a5dd0ba` (same as EXP-000/001) |
| Compared against | EXP-001 |

> **Dirty-run note:** the change under test (`app/rag/retriever.py`, plus `rank-bm25` and `scikit-learn` in `pyproject.toml`) was uncommitted when these runs were made. The only other uncommitted change was the `__main__` test query in `app/rag/chain.py`, which doesn't affect evals. Replace the commit above with the hash of the commit containing this retriever.

**Hypothesis / prediction:** BM25 matches exact terms that dense search blurs:
- sf-11 (DPDP / GDPR / PCI-DSS) and sf-03 ("Customer Acquisition Cost") should recover; sf-02 and sf-06 likely too.
- entity_typo may drop, because BM25 can't match "Arav" to "Aarav".
- Tier 1 evidence recall at k=5 should go above 0.70.

**Change** (`app/rag/retriever.py`):
- **One global BM25 index** (`BM25Retriever`, `rank_bm25` BM25Okapi) over all 334 chunks, read back from Chroma at startup, so both retrievers see identical chunks.
- **Tokenizer:** lowercase; the regex `[a-z0-9]+(?:-[a-z0-9]+)*` keeps hyphenated terms like `pci-dss` whole; stopwords are removed using scikit-learn's `ENGLISH_STOP_WORDS`.
- **Per query:**
  - Dense top 20, with its existing role filter.
  - BM25 ranks all chunks, keeps only the role's allowed categories, and takes the top 20.
  - The two lists are fused with RRF (`1/(60 + rank)`, ranks counted from 1, equal weights), and the top k=5 are returned.
- The scope guardrail (`get_relevance_score`) is unchanged and stays dense-only.
- `RETRIEVAL_STRATEGY = "hybrid-bm25-rrf"`.

**Variants tried and rejected:**

| Variant | Outcome |
|---|---|
| **Per-category BM25** (one index per category, each passed to RRF as its own list) | Rejected. Each allowed category's #1 BM25 hit gets an RRF score of 1/61 regardless of relevance, so `c_level` (5 lists against 1 dense list) weighted BM25 5:1, and irrelevant categories' top hits entered the top 5. An example: `financial_summary-11` for a compliance question. Measured (dirty run): Tier 1 0.650 @k=5, 0.850 @k=15; Tier 2 pass rate 0.375. |
| In-memory simulation of the fix (Tier 1, no LLM) | Per-category, no stopwords: 0.650 / 0.850 · per-category + stopwords: 0.650 / 0.900 · **global + role filter + stopwords: 0.700 / 0.904** (k=5 / k=15). This used a hand-written list of about 45 stopwords. |
| **Void run** `20261005-111522.json` | A leftover `if category in bm25:` check was always False, so BM25 never ran and the run measured dense-only retrieval. Its Tier 1 results matched EXP-001 exactly. Not cited as a result, but see the noise note below. |

**Results** (k=5):

| Tag | n (T1/T2) | Evidence recall | Δ | Pass rate | Δ | Mean score (T2) | Δ |
|---|---|---|---|---|---|---|---|
| single_fact | 11/11 | 0.636 | 0 | 0.545 | 0 | 0.591 | 0 |
| aggregate | 1/5 | 0.750 | +0.500 | 0.000 | 0 | 0.150 | +0.100 |
| multi_doc | 3/3 | 0.417 | 0 | 0.000 | 0 | 0.367 | 0 |
| multi_chunk | 2/2 | 0.500 | 0 | 0.500 | 0 | 0.500 | 0 |
| entity_typo | 3/3 | 0.833 | −0.167 | 0.667 | 0 | 0.667 | 0 |
| **overall** | 20/24 | **0.625** | **0** | **0.375** | **0** | 0.473 | +0.021 |

**Tier 1 at k=15: 0.904** (EXP-001: 0.838), with completeness 0.80 (0.75). single_fact goes from 0.818 to 0.939.

Tier 2 overall: 9 PASS / 4 PARTIAL / 11 FAIL with **7 refused**, against 9 / 4 / 11 with 10 refused in EXP-001.

**Rows that flipped:**

| Row | Tier 1 @k=5 | Tier 2 | Cause |
|---|---|---|---|
| sf-06 | 0 → 1.0 | FAIL → **PASS** | BM25 matched "databases" / "data layer"; the answer lists all four stores. |
| agg-03 | 0.25 → 0.75 | PARTIAL (0.25 → 0.75) | BM25 matched "HR" in the HR rows: 3 of the 4 HR managers named. |
| **sf-08** | **1.0 → 0** | **PASS → FAIL** | **Regression.** The core values chunk is dense rank #1 but has **no BM25 hit**: the words "Core Values" exist only in its `Header 3` metadata, not in its text. Chunks ranked moderately by *both* retrievers (2/65 ≈ 0.031) outscore a dense-only #1 (1/61 ≈ 0.016), so it fell out of the top 5. |
| typo-02 | 1.0 → 0.5 | FAIL → FAIL | One of the two Isha Chowdhury rows was pushed out; the answer refuses as before. |
| sf-03 (k=15 only) | 0 → 1.0 @k=15 | FAIL → FAIL | The CAC chunk is now in the top 15 but not the top 5. The answer is now **confidently wrong** ("CPA $11.36") instead of a refusal. |
| sf-11 (k=15 only) | 0 → 0.33 @k=15 | FAIL → FAIL | Still mostly missing. The query words "compliance frameworks" aren't in the chunk text. |

**Layer B:** 0 failures / 30 rows. RBAC holds: BM25 filters to the allowed categories before fusion.

**Ops:**

| | EXP-001 | EXP-002 | Δ |
|---|---|---|---|
| Prompt tokens per run | 22,599 | 22,801 | +1% |
| Cost per request | $0.000207 | $0.000211 | +2% |
| Avg / p95 latency | 3775 / 9221 ms | 3933 / 9506 ms | within noise |

BM25 over 334 chunks adds negligible latency. Startup builds the index once.

**Observations:**
- **Hybrid search improves the candidate pool, not the top 5.**
  - At k=15, evidence recall rises from 0.838 to 0.904.
  - At k=5 it's flat: 2 rows gained (sf-06, agg-03) and 2 lost (sf-08, typo-02).
  - So the main value of hybrid search here is as a candidate generator for a reranker.
- **Equal-weight RRF penalizes single-retriever wins.** A chunk that only one retriever ranks #1 (sf-08 dense, typo rows dense) loses to chunks both retrievers rank in the middle. A reranker, or RRF weights, would address this.
- **Header text is invisible to retrieval. This is a new root cause.** `MarkdownHeaderTextSplitter` moves headings into metadata, so phrases like "Core Values" (sf-08), and likely "Compliance" (sf-11) and quarter labels, never reach the embedding or the BM25 index. Prepending the header path to each chunk's text ("contextual chunk headers") is a cheap ingestion fix and a strong candidate experiment.
- **Aggregates got more confidently wrong.** Aggregate refusals dropped from 2 to 0: agg-01 now says "three employees", and agg-04 says "one employee". BM25 surfaces more HR rows, and the model counts whatever it sees. A prompt rule against counting is now more urgent.
- **Measured noise floor for Tier 2 is about 2 rows.** In the void run, retrieval was identical to EXP-001, yet 2 rows changed verdict (multi-02 and mc-02, FAIL → PARTIAL). A pass-rate difference of ±0.083 is within noise.

**Stage A decision:** keep hybrid retrieval as the candidate generator. It's flat at k=5 but lifts k=15 recall to 0.904 with no ops cost. The header root cause found here led to Stage B.

### Stage B — Contextual chunk headers (on top of Stage A)

| | |
|---|---|
| Date | 2026-10-05 |
| Commit | `28c75cf` + uncommitted Stage A and Stage B changes (**dirty**). Replace with the commit containing both. |
| Results | Tier 1: `eval/results/retrieval-20261005-120001.json` (k=5) · `retrieval-20261005-120024.json` (k=15) · Tier 2: `eval/results/20261005-120129.json` |
| Compared against | Stage A (`retrieval-20261005-112550/112615.json`, `20261005-112707.json`) |

> The manifest still reads `retrieval_strategy: "hybrid-bm25-rrf"` because the label wasn't updated for this run. The chunk *text* differs from Stage A while `index_chunk_count` stays 334, so **the manifest alone can't tell Stage A and Stage B runs apart.** Use the file names listed here. Set `RETRIEVAL_STRATEGY = "hybrid-bm25-rrf+ctx-headers"` before the next run.

**Hypothesis / prediction:**
- `MarkdownHeaderTextSplitter(strip_headers=True)` moves headings into metadata, where neither retriever can see them. Putting them back in the text should recover sf-08 ("Core Values" is only in `Header 3`) at k=5.
- It should also improve sf-11 and the quarter-labelled rows (sf-02, mc-02), whose labels live in headings like "Q2 - April to June 2024".
- entity_typo should be unchanged, because HR rows have no headings.

**Change** (`app/ingestion/chunking.py`):
- After both splitters run, each markdown chunk's text is prefixed with its heading path built from `Header 1`→`Header 4`, for example: `Employee Handbook > Welcome & Introduction > Core Values\n- **Integrity**: ...`
- It's prepended *after* splitting, so every sub-chunk of a long section gets the path, not only the first.
- HR rows are unchanged. The index was rebuilt; the chunk count stays 334.

**Results** (k=5):

| Tag | n (T1/T2) | Evidence recall | Δ vs A | Pass rate | Δ vs A | Mean score (T2) | Δ vs A |
|---|---|---|---|---|---|---|---|
| single_fact | 11/11 | **0.909** | +0.273 | **0.727** | +0.182 | 0.841 | +0.250 |
| aggregate | 1/5 | 0.750 | 0 | 0.000 | 0 | 0.150 | 0 |
| multi_doc | 3/3 | 0.500 | +0.083 | 0.000 | 0 | 0.367 | 0 |
| multi_chunk | 2/2 | 0.750 | +0.250 | 0.500 | 0 | 0.875 | +0.375 |
| entity_typo | 3/3 | 0.833 | 0 | 0.667 | 0 | 0.667 | 0 |
| **overall** | 20/24 | **0.812** | **+0.187** | **0.458** | **+0.083** | **0.619** | +0.146 |

- **Tier 1 at k=15:** 0.912 (Stage A: 0.904), with completeness 0.85 (0.80).
- **Tier 2 overall:** 11 PASS / 6 PARTIAL / 7 FAIL with **5 refused**, against 9 / 4 / 11 with 7 refused in Stage A.

**Rows that flipped:**

| Row | Tier 1 @k=5 | Tier 2 | Cause |
|---|---|---|---|
| sf-02 | 0 → 1.0 | FAIL → **PASS** | The "Q2 - April to June 2024" heading is now in the net-income chunk's text. |
| sf-08 | 0 → 1.0 | FAIL → **PASS** | "Core Values" is now in the chunk text. This fixes the Stage A regression. |
| sf-11 | 0 → 1.0 | FAIL → **PASS** | The compliance heading is now matched. The answer lists ISO 27001 as well as DPDP, GDPR and PCI-DSS. |
| mc-02 | 0 → 0.5 | FAIL → PARTIAL (0.75) | Q1, Q2 and Q4 revenue are now retrieved; Q3 is still missing. |
| multi-02 | 0.25 → 0.5 | FAIL → FAIL | More quarters retrieved, but the answer still refuses. |
| sf-06 | 1.0 → 1.0 | PASS → PARTIAL (0.75) | Retrieval is unchanged; the answer omitted S3. This is answer-model variation, within the noise floor. |
| sf-03 (k=15) | 1.0 → 0 @k=15 | FAIL → FAIL | The CAC chunk dropped out of the top 15; the quarterly CPA chunks outrank it. The answer lists quarterly CPAs instead of the $150 CAC. |

**Layer B:** 0 failures / 30 rows.

**Ops:**

| | Stage A | Stage B | Δ |
|---|---|---|---|
| Prompt tokens per run | 22,801 | 24,671 | +8% (header paths in every chunk) |
| Cost per request | $0.000211 | $0.000216 | +2% |
| Avg / p95 latency | 3933 / 9506 ms | 4782 / 12933 ms | +0.8 s / +3.4 s. Probably mostly Groq variance, but watch it. |

**Observations:**
- **This is the largest single improvement so far:**
  - Tier 1 @k=5 rose 0.625 → 0.812 and single_fact 0.636 → 0.909.
  - Tier 2 pass rate rose 0.375 → 0.458, a 2-row net gain, which is at the noise floor.
  - The +3 PASS rows (sf-02, sf-08, sf-11) each have a matching retrieval fix, so it's a real improvement, not noise.
- **The top-5 / top-15 gap has narrowed:** 0.812 @k=5 against 0.912 @k=15. A reranker now has less to recover than at Stage A (0.625 against 0.904).
- **Remaining failures are no longer mainly retrieval:**
  - **Aggregates** (0/5): counting over retrieved rows. Needs a prompt rule against counting, or a structured path.
  - **Partial multi-part answers** (multi-01/02/03, mc-02, sf-07): evidence is mostly retrieved, but answers cover only part of it or refuse the rest. This is answer-model / prompt behaviour.
  - **sf-03:** the CAC chunk is outranked by similar quarterly CPA chunks. A reranker target.
  - **typo-02:** one of the two Isha Chowdhury rows is ranked low, and the model refuses.

**Decision:** **keep both stages.** EXP-002 = hybrid BM25 + RRF + contextual chunk headers is the new baseline for EXP-003 (reranker over the top 20 fused candidates, keeping the top 5). Expect smaller gains than Stage A's gap suggested; the remaining k=5 misses are sf-03, the multi_doc rows, mc-02 and typo-02.

---

## EXP-003 — Prompt rule: no counting or totalling over retrieved records

| | |
|---|---|
| Date | 2026-11-20 |
| Commit | *(filled in after the run)* |
| Results | *(filled in after the run)* |
| Dataset | sha256 `9537e4eb…a5dd0ba` (unchanged) |
| Compared against | EXP-002 Stage B (`eval/results/20261005-120129.json`) |

**Hypothesis / prediction** (written before the change):
- **The problem:** in EXP-002 B, 3 of 5 aggregate rows were *confidently wrong*: agg-02 "five employees in Sales" (truth 15), agg-04 "one employee" (23), agg-05 "4 employees" (10). The model counts the handful of HR rows it was given and reports that as the total.
- **The change:** a prompt rule saying the context holds only a sample of records, so it must not count, sum or average across them unless the documents state the figure directly. It should say so instead, with a reply starting "I don't have", so Tier 2's `refused` flag catches it.
- **Prediction:**
  - aggregate pass rate stays 0/5, since none of these can be answered from retrieved records;
  - confidently wrong numeric answers on aggregate rows drop from 3 to 0;
  - aggregate `refused` rises from 1 to about 4;
  - agg-03 (*list* the HR team) is at risk of being over-refused, which would be a regression worth watching;
  - every other tag is unchanged within the noise floor (±2 rows);
  - single facts that quote a stated total, like sf-01's "$9.4 billion", must still pass;
  - the retrieval check (Tier 1) is identical, because retrieval code is untouched.
