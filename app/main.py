from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Imported first, and for its side effect: loading .env into os.environ before
# anything else (LangSmith, huggingface_hub, etc.) reads it. See the comment in
# app/monitoring/tracing.py for why this can't just be pydantic-settings.
import app.monitoring.tracing  # noqa: F401

from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.core.config import get_settings
from app.monitoring.cost_tracker import ensure_table

app = FastAPI(title="RAG Chatbot with RBAC")

# The frontend is served from a different origin in production (Static Web
# Apps), so the browser needs CORS. Exact origins only, never "*": the API
# takes a bearer token, and only our own frontend should be calling it.
_origins = [o.strip().rstrip("/") for o in get_settings().cors_origins.split(",") if o.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

if get_settings().database_url:
    try:
        ensure_table()
    except Exception as exc:
        # Cost logging is a side feature: a paused or unreachable database
        # (Supabase pauses idle free-tier projects) must not stop chat from
        # starting. log_cost() already fails soft per request.
        print(f"[cost_tracker] database unavailable at startup, cost logging will fail until it's back: {exc}")
else:
    print("[cost_tracker] DATABASE_URL not set — cost logging disabled.")

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to the RAG Chatbot with RBAC API!"}

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(chat_router)
