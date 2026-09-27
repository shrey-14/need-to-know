# Per-request token/cost logging to Postgres (Supabase). Monitoring phase.
import psycopg

from app.core.config import get_settings

settings = get_settings()

# Groq pricing for the configured model (openai/gpt-oss-120b), per Groq's own
# docs as of writing: https://console.groq.com/docs/model/openai/gpt-oss-120b
# Update these if GROQ_MODEL changes to a differently-priced model.
PRICE_PER_MILLION_INPUT_TOKENS = 0.15
PRICE_PER_MILLION_OUTPUT_TOKENS = 0.60


def ensure_table() -> None:
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cost_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
                role TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                estimated_cost NUMERIC NOT NULL
            )
            """
        )
        # CREATE TABLE IF NOT EXISTS won't add columns to a table that already
        # exists, so later columns are migrated separately. Nullable, so rows
        # logged before this column existed stay valid.
        conn.execute("ALTER TABLE cost_log ADD COLUMN IF NOT EXISTS latency_ms INTEGER")


def log_cost(
    role: str, prompt_tokens: int, completion_tokens: int, latency_ms: int | None = None
) -> None:
    """Record one LLM request's token usage, estimated cost, and end-to-end
    latency. Never raises — a logging failure must not break the chat response
    it's logging."""
    estimated_cost = (
        prompt_tokens * PRICE_PER_MILLION_INPUT_TOKENS / 1_000_000
        + completion_tokens * PRICE_PER_MILLION_OUTPUT_TOKENS / 1_000_000
    )
    try:
        with psycopg.connect(settings.database_url, autocommit=True) as conn:
            conn.execute(
                """
                INSERT INTO cost_log (role, prompt_tokens, completion_tokens, estimated_cost, latency_ms)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (role, prompt_tokens, completion_tokens, estimated_cost, latency_ms),
            )
    except Exception as exc:
        print(f"[cost_tracker] failed to log cost: {exc}")


