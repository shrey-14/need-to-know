# LangSmith callback wiring for request/retrieval tracing. Monitoring phase.
#
# pydantic-settings parses .env into our own Settings object only — it never
# exports those values into os.environ. LangChain's tracing doesn't go through
# our Settings class at all; it reads LANGCHAIN_TRACING_V2 / LANGCHAIN_API_KEY /
# LANGCHAIN_PROJECT directly from os.environ. Without this load_dotenv() call,
# tracing silently does nothing, no matter what .env says.
from dotenv import load_dotenv

load_dotenv()

def trace_config(role: str) -> dict:
    """Per-request LangSmith metadata, so traces are filterable by role in the UI.

    Pass as the `config` argument to any LangChain Runnable's .invoke(), e.g.
    llm.invoke(prompt, config=trace_config(role)).
    """
    return {"tags": [role], "metadata": {"role": role}}
