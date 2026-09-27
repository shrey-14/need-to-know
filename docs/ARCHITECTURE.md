# Architecture

Two separate flows: an offline flow that builds the knowledge base, and a live flow
that answers a user's question.

## 1. Offline flow — building the knowledge base

Runs once, and re-run whenever `data/` changes.

```
data/<category>/*.md, *.csv
        │
        ▼
  loaders.py        (read markdown as text; read hr_data.csv row-by-row via pandas)
        │
        ▼
  chunking.py        (split markdown by headers, keep HR rows as one doc each)
        │  each chunk gets metadata: {category: "finance"|"hr"|..., source: filename}
        ▼
  embedding model     (sentence-transformers, local, free)
        │
        ▼
  Chroma vector store (persisted to disk at .chroma/)
```

## 2. Live flow — answering a user's question

```
React (Login) --POST /login {user,pass}--> FastAPI
                                              │ checks users.yaml (bcrypt)
                                              ▼
                                     issues JWT {username, role}
React (Chat) <---------------------------------┘

React (Chat) --POST /chat {query} + JWT-------> FastAPI
                                              │
                                    1. verify JWT, extract role
                                              │
                                    2. guardrails/scope.py:
                                       is this query in-scope?
                                       ──No──> return canned refusal, STOP
                                       ──Yes─▼
                                    3. roles.allowed_categories(role)
                                       -> retriever.py queries Chroma
                                          WITH metadata filter on category
                                              │
                                    4. chain.py: build prompt
                                       (retrieved chunks + question)
                                       -> Groq LLM (Llama 3.x)
                                              │
                                    5. guardrails/pii.py:
                                       redact PII if role shouldn't see it
                                              │
                                    6. monitoring: log tokens/cost to
                                       SQLite + trace to LangSmith;
                                       check daily cost threshold
                                              │
                                              ▼
                            {answer, sources: [...], role} back to React
```

Every box above corresponds to a stubbed file under `app/` — see
[BUILD_GUIDE.md](BUILD_GUIDE.md) for the order to implement them in.

## Roles & Data Access

| Role | Access |
|---|---|
| `finance` | `data/finance/*` |
| `marketing` | `data/marketing/*` |
| `hr` | `data/hr/*` |
| `engineering` | `data/engineering/*` |
| `employee` | `data/general/*` only |
| `c_level` | `data/*` |

Authoritative mapping lives in [app/core/roles.py](../app/core/roles.py).

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: React (Vite + TypeScript)
- **Orchestration**: LangChain
- **LLM**: Llama 3.x via Groq (free tier)
- **Embeddings**: local `sentence-transformers/all-MiniLM-L6-v2`
- **Vector store**: ChromaDB (persisted locally)
- **Auth**: `users.yaml` (bcrypt-hashed) + JWT
- **Guardrails**: PII redaction, out-of-scope query detection
- **Evals**: Ragas (faithfulness, answer relevancy, context precision/recall)
- **Monitoring**: LangSmith tracing + SQLite-backed token/cost logging with alert thresholds
- **CI/CD**: GitHub Actions (lint + tests + eval gate → build → deploy)
- **Cloud**: Azure Container Apps
