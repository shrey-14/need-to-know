# Test environment: no secrets, no network services. Set before any app module
# is imported, so a developer's local .env (real Groq key, real database) is
# never used: pydantic-settings and load_dotenv both let real environment
# variables win over .env, and an empty string still counts as set. This makes
# local runs behave exactly like CI, which has no secrets at all.
import os

os.environ["GROQ_API_KEY"] = ""
os.environ["DATABASE_URL"] = ""
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["ALERT_EMAIL_TO"] = ""
os.environ["CORS_ORIGINS"] = ""
os.environ["JWT_SECRET_KEY"] = "test-only-secret"
