from fastapi import FastAPI

# Imported first, and for its side effect: loading .env into os.environ before
# anything else (LangSmith, huggingface_hub, etc.) reads it. See the comment in
# app/monitoring/tracing.py for why this can't just be pydantic-settings.
import app.monitoring.tracing  # noqa: F401

from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.core.config import get_settings
from app.monitoring.cost_tracker import ensure_table

app = FastAPI(title="RAG Chatbot with RBAC")

if get_settings().database_url:
    ensure_table()
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
