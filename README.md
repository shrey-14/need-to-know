# RAG Chatbot with RBAC

Internal chatbot for FinSolve Technologies that answers questions over company data
(finance, marketing, HR, engineering, general policies) while enforcing role-based
access control, PII/out-of-scope guardrails, cost tracking, and automated evals on
every deploy.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full request-flow diagram

## Roles & Data Access

| Role | Access |
|---|---|
| `finance` | `data/finance/*` |
| `marketing` | `data/marketing/*` |
| `hr` | `data/hr/*` |
| `engineering` | `data/engineering/*` |
| `employee` | `data/general/*` only |
| `c_level` | all of the above |

See [app/core/roles.py](app/core/roles.py) for the authoritative mapping.

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

## Project Status

This repo is scaffolded but not yet functional end-to-end. Build order:

- [ ] 1. Scaffold (done)
- [ ] 2. Ingestion & vector store (`app/ingestion/`)
- [ ] 3. Core RAG + RBAC retrieval (`app/rag/`)
- [ ] 4. Auth (`app/core/security.py`, `app/api/routes_auth.py`)
- [ ] 5. Guardrails (`app/guardrails/`)
- [ ] 6. Frontend (`frontend/`)
- [ ] 7. Monitoring & cost tracking (`app/monitoring/`)
- [ ] 8. Evaluation (`eval/`)
- [ ] 9. CI/CD + Azure deploy (`infra/`, `.github/workflows/`)
- [ ] 10. Docs polish

## Setup (once dependencies land — Phase 2+)

### Backend

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in GROQ_API_KEY at minimum
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Ingestion (build the vector index from `data/`)

```bash
python -m app.ingestion.build_index
```

## Repository Layout

```
app/            FastAPI backend: api, core (config/security/roles), ingestion, rag, guardrails, monitoring
frontend/       React (Vite + TS) chat UI
data/           Source documents, one subfolder per access category
eval/           Ragas eval dataset + runner
users/          Demo user/role credentials for local dev
infra/          Dockerfiles, docker-compose, Azure deploy assets
.github/        CI/CD workflow
```
