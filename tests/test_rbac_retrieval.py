"""Access control at the retrieval layer: the product's core guarantee.

For every role, questions aimed at every department must only ever retrieve
chunks from that role's allowed categories, from both the dense and the BM25
side of hybrid search. Needs the built index (python -m app.ingestion.build_index)
but no LLM.
"""
import pytest

from app.core.roles import ROLE_ACCESS, allowed_categories
from app.rag.retriever import get_relevant_documents

# One probe per department, phrased to pull hard towards it. If retrieval ever
# leaked across a boundary, these are the questions that would show it.
PROBES = {
    "finance": "What was FinSolve's revenue and net income in each quarter of 2024?",
    "marketing": "What was the 2024 marketing budget and customer acquisition cost?",
    "hr": "What is the salary, date of birth and leave balance of each employee?",
    "engineering": "Which databases and deployment strategy does the platform use?",
    "general": "What is the company's leave policy and code of conduct?",
}

# k=20 reaches deep into both rankings, so a BM25-only or dense-only leak at a
# low rank would still be caught.
K = 20


@pytest.mark.parametrize("role", sorted(ROLE_ACCESS))
@pytest.mark.parametrize("department", sorted(PROBES))
def test_retrieval_never_crosses_role_boundary(role: str, department: str) -> None:
    allowed = set(allowed_categories(role))
    docs = get_relevant_documents(PROBES[department], role, k=K)
    leaked = {d.metadata["category"] for d in docs} - allowed
    assert not leaked, f"{role} retrieved {sorted(leaked)} for a {department} question"


@pytest.mark.parametrize("role", sorted(ROLE_ACCESS))
def test_role_still_reaches_its_own_departments(role: str) -> None:
    # Guards against the boundary test passing vacuously (e.g. a broken filter
    # that returns nothing at all).
    for department in allowed_categories(role):
        docs = get_relevant_documents(PROBES[department], role, k=K)
        assert any(d.metadata["category"] == department for d in docs), (
            f"{role} could not retrieve its own {department} documents"
        )


def test_unknown_role_retrieves_nothing() -> None:
    assert get_relevant_documents(PROBES["general"], "intern", k=K) == []
