from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_small_model: str = "openai/gpt-oss-20b"
    qwen_model: str = "qwen/qwen3.8-27b"

    # Auth
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Vector store
    chroma_persist_dir: str = "./.chroma"
    embedding_model: str = "BAAI/bge-base-en-v1.5"

    # Monitoring
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "rag-chatbot-rbac"
    database_url: str = ""  # Supabase Postgres connection string
    daily_cost_alert_usd: float = 1.0

    # Slack
    slack_webhook_url: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
