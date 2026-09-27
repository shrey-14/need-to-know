# Out-of-scope / off-topic query detector, run before hitting the retriever. Guardrails phase.
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.rag.retriever import vectorstore

settings = get_settings()
llm = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key)

# Layer 1 thresholds on the relevance score (0-1, higher = more relevant to the
# corpus). Tune these by running this file directly and looking at what scores
# real in-scope vs. out-of-scope questions actually produce.
LOW_THRESHOLD = 0.2   # below this: confidently unrelated, reject without calling the LLM
HIGH_THRESHOLD = 0.5  # above this: confidently relevant, skip the classifier call

CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You classify whether a question is about FinSolve Technologies' internal "
        "business data (finance, HR, marketing, engineering, or company policies). "
        "Reply with exactly one word: IN_SCOPE or OUT_OF_SCOPE.",
    ),
    ("human", "{question}"),
])


def get_relevance_score(query: str) -> float:
    """Layer 1: how closely does this query relate to anything in the corpus at all?"""
    results = vectorstore.similarity_search_with_relevance_scores(query, k=1)
    if not results:
        return 0.0
    _, score = results[0]
    return score


def classify_scope(query: str) -> bool:
    """Layer 2: cheap LLM call, only used for the ambiguous middle band."""
    response = llm.invoke(CLASSIFICATION_PROMPT.invoke({"question": query}))
    return response.content.strip().upper() == "IN_SCOPE"



def is_out_of_scope(score: float, query: str) -> bool:

    if score < LOW_THRESHOLD:
        return True
    if score > HIGH_THRESHOLD:
        return False

    # Ambiguous middle band — escalate to the classifier to break the tie.
    return not classify_scope(query)


if __name__ == "__main__":
    test_queries = [
        "What was FinSolve's total revenue in 2024?",
        "Write me a poem about the ocean.",
        "hi",
        "What is the leave policy?",
        "How does FinSolve's marketing spend compare to Stripe's?",
    ]
    for q in test_queries:
        score = get_relevance_score(q)
        print(f"{q!r:60} score={score:.3f}  out_of_scope={is_out_of_scope(score, q)}")
