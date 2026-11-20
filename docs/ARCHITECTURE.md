# Architecture

FinSolve Assistant has two flows:
- an **offline flow** that turns the documents in `data/` into a searchable index;
- a **live flow** that answers one question for one signed-in role.

Access control is enforced inside the live flow at retrieval, the point where documents are selected, not afterwards.

## 1. Offline flow: building the index

Run `python -m app.ingestion.build_index`. Re-run it whenever `data/` or the chunking settings change.

```
data/<category>/*.md, hr_data.csv          category = folder name: finance | marketing | hr | engineering | general
        │
        ▼
loaders.py      markdown read as text; hr_data.csv → one document per employee
        │
        ▼
chunking.py     markdown: split by headings (#–####), then 800-char chunks, 150 overlap
                each chunk's text is prefixed with its heading path, e.g.
                "Employee Handbook > Welcome & Introduction > Core Values"
                HR rows are left whole (one row = one chunk)
                metadata on every chunk: category, source, chunk_id
        │
        ▼
build_index.py  deletes the old collection, then embeds with BAAI/bge-base-en-v1.5
                (local, normalised) into Chroma at .chroma/ (collection finsolve_docs)
```

**Two non-obvious decisions:**
- **Heading paths are put back into the chunk text.** `MarkdownHeaderTextSplitter` moves headings into metadata, where neither search method can see them. Without this, a chunk under "Core Values" doesn't contain the words "core values". This was the largest single retrieval gain: top-5 evidence recall went from 63% to 81% (EXP-002, [EXPERIMENTS.md](EXPERIMENTS.md)).
- **The collection is deleted before re-indexing.** Chunks are written by ID, so re-chunking into fewer pieces would otherwise leave old chunks behind and mix two chunk sizes in one index.

## 2. Live flow: answering a question

```
Browser (React)                                  FastAPI
───────────────                                  ───────
Sign in ── POST /login {username, password} ──►  routes_auth.py
                                                 bcrypt check against users/users.yaml
        ◄──────────── JWT {sub, role, exp} ──────

Ask ────── POST /chat {question} + Bearer JWT ─► routes_chat.py → get_current_user (JWT verified)
                                                 rag/chain.py: answer_question(question, role)
                                                  │
  1. Scope guardrail       guardrails/scope.py
                           relevance score of the closest chunk in the whole corpus:
                           < 0.2 out of scope · > 0.5 in scope · in between → LLM classifier
                           out of scope → "I don't have access to that information." (stop)
                                                  │
  2. Hybrid retrieval      rag/retriever.py, categories = allowed_categories(role)
                           dense:  Chroma similarity search, filter category ∈ categories, top 20
                           BM25:   one global index (stopwords removed, hyphenated terms kept whole),
                                   results filtered to categories, top 20
                           fuse:   reciprocal rank fusion (1 / (60 + rank)), top 5
                           nothing retrieved → decline (stop)
                                                  │
  3. Generation            rag/prompts.py + Groq openai/gpt-oss-120b
                           rules: answer only from context · cite every claim as [Source: file]
                           · say "I don't have that information" when unsupported
                           · never count or total records the documents don't state
                                                  │
  4. PII redaction         guardrails/pii.py: emails, ₹ salaries, dates, employee IDs masked
                           unless the role can read HR
                                                  │
  5. Monitoring            LangSmith trace · cost_log row (tokens, cost, role, latency_ms)
                           in Postgres · daily cost threshold → at most one alert email per day
                                                  │
        ◄────────────────── {answer, sources} ───┘
```

### Where access control is enforced

| Layer | What it guarantees |
|---|---|
| **Retrieval (the enforcement point)** | Both dense and BM25 search are limited to the role's categories *before* anything reaches the model, so restricted text is never in the prompt. Evaluated in every run: 0 cross-role leaks. |
| PII redaction | A second layer that masks HR-style personal data in answers for roles without HR access. |
| Scope guardrail | Rejects off-topic questions cheaply. It scores relevance against the *whole* corpus on purpose, because it only decides in-scope versus out-of-scope and never returns content. |
| Frontend (`frontend/src/roles.ts`) | Display only: it shows the user which departments their role reads. It is never trusted for access. |

The role → category mapping lives in one place, [app/core/roles.py](../app/core/roles.py):

| Role | Can read |
|---|---|
| finance | finance, general |
| marketing | marketing, general |
| hr | hr, general |
| engineering | engineering, general |
| employee | general |
| c_level | all categories |

## 3. Frontend

React + Vite + TypeScript. There are two routes, `/login` and `/chat`, and `RequireAuth` protects `/chat`.

- **Requests:** the JWT is kept in `localStorage` and sent as a Bearer token. In development, `/api/*` is proxied to FastAPI (`vite.config.ts`), because the frontend's own routes are also named `/login` and `/chat`.
- **Citations** (`frontend/src/citations.ts`):
  - It parses the model's inline citations in all the shapes the model produces: `[Source: …]`, `【Source: …】`, `(Sources: a; b)`, back-to-back citations, and citations with section paths.
  - Each one becomes a numbered note, keyed by document and section.
  - Documents that were retrieved but never cited are listed separately under "Also consulted", without a number.
- **Markdown:** answers render as GitHub-flavoured markdown (`remark-gfm`). Raw HTML from the model, such as `<br>` in table cells, is rendered and then sanitised (`rehype-raw` + `rehype-sanitize`).
- **Declines:** the backend's decline text doesn't say *why* it declined, so the UI shows a single "Not answered" state that explains both possibilities (an off-topic question, or a department the role can't read).

The visual design system is documented in [DESIGN.md](../DESIGN.md).

## 4. Monitoring

| What | Where | Notes |
|---|---|---|
| Traces | LangSmith | Turned on by `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY`; eval runs go to a separate project |
| Cost and latency | `cost_log` table in Postgres (Supabase) | One row per request that reaches the LLM. The table and the `latency_ms` column are created on startup. If the database is unreachable, startup and chat continue. |
| Alerts | SMTP email (`monitoring/alerts.py`) | Sent when today's cost passes `DAILY_COST_ALERT_USD`. At most one per day; provider-agnostic (Gmail app password, or any SMTP provider). |

All monitoring is optional: the app runs with none of it configured.

## 5. Evaluation

The `eval/` folder holds a 30-row test set (`eval_dataset.jsonl`). Each answerable row has:
- `evidence`: text that must appear in the retrieved chunks;
- `must_contain`: facts that must appear in the answer.

| Tier | Runner | Checks |
|---|---|---|
| 1 | `eval/retrieval_check.py` | Evidence recall in the top-k chunks. No LLM calls, deterministic. `--k` sweeps the cut-off; `--validate` checks every evidence string exists in the index. |
| 2 | `eval/run_evals.py` | Answer facts (pass / partial / fail), plus hard gates: no cross-role leaks, correct refusals and out-of-scope handling. |
| 3 | `eval/run_evals.py --ragas` | LLM-judged Ragas metrics, for milestones only. |

Every run writes `eval/results/<run_id>.json` with a manifest: git commit, a flag for uncommitted changes, configuration, the index's chunk count and a hash of the dataset. The experiment log is [EXPERIMENTS.md](EXPERIMENTS.md).

## 6. File map

```
app/
  main.py                 FastAPI app; startup table check (fails soft)
  api/                    routes_auth.py (/login), routes_chat.py (/chat)
  core/                   config.py (settings from .env), security.py (bcrypt, JWT), roles.py (role → categories)
  ingestion/              loaders.py, chunking.py, build_index.py
  rag/                    retriever.py (hybrid + RRF), prompts.py, chain.py (the pipeline above)
  guardrails/             scope.py, pii.py
  monitoring/             tracing.py, cost_tracker.py, alerts.py
frontend/src/
  pages/                  Login.tsx, Chat.tsx (+ CSS modules)
  citations.ts            citation parsing → numbered notes
  departments.ts, roles.ts  display metadata and access map (display only)
eval/                     eval_dataset.jsonl, checks.py, retrieval_check.py, run_evals.py, results/
data/                     source documents, one folder per category
users/users.yaml          demo users (bcrypt hashes)
```

## 7. Known limitations

- **Questions that need counts or totals across records can't be answered** from top-5 retrieval. They are declined on purpose (prompt rule 4). A real fix would be a structured path: precomputed summaries or a tool or SQL route.
- **Each question is answered on its own;** there is no memory across turns.
- **The scope guardrail's LLM classifier is non-deterministic for borderline questions,** so the same question can occasionally be declined in one run and answered in another (seen in EXP-003).
- **Not yet built:** Docker images, CI and cloud deployment (`infra/` and `.github/workflows/` are placeholders).
