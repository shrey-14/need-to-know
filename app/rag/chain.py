# Retrieval + prompt + Groq LLM call, returns {answer, sources}. RAG phase.
import time

from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.rag.prompts import prompt_template, format_context
from app.rag.retriever import get_relevant_documents
from app.guardrails.scope import is_out_of_scope, get_relevance_score
from app.guardrails.pii import redact_pii
from app.monitoring.tracing import trace_config
from app.monitoring.cost_tracker import log_cost
from app.monitoring.alerts import check_daily_cost_threshold

settings = get_settings()
llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key)


def answer_question(query: str, role: str) -> dict:
    start = time.perf_counter()

    out_of_scope = is_out_of_scope(get_relevance_score(query), query)
    
    if out_of_scope:
        return {"answer": "I don't have access to that information.", "sources": [], "contexts": []}
    
    else:
        docs = get_relevant_documents(query, role)

        if not docs:
            return {"answer": "I don't have access to that information.", "sources": [], "contexts": []}

        context_text = format_context(docs)
        filled_prompt = prompt_template.invoke({"context": context_text, "question": query})
        response = llm.invoke(filled_prompt, config=trace_config(role))

        response.content = redact_pii(response.content, role)

        sources = sorted({doc.metadata["source"] for doc in docs})

        contexts = [
            {"text": doc.page_content, "category": doc.metadata["category"], "source": doc.metadata["source"]}
            for doc in docs
        ]

        # Measured before logging, so it's the request's own work, not the DB write.
        latency_ms = round((time.perf_counter() - start) * 1000)
        token_usage = response.response_metadata.get("token_usage", {})
        log_cost(
            role,
            prompt_tokens=token_usage.get("prompt_tokens", 0),
            completion_tokens=token_usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
        )
        check_daily_cost_threshold()

        return {"answer": response.content, "sources": sources, "contexts": contexts}


if __name__ == "__main__":
    result = answer_question(query="What is the company's leave policy?", role="hr")
    print(result["answer"])
    print(result["sources"])
    print(result["contexts"])


