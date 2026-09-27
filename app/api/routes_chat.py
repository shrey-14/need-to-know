# POST /chat -> role-gated RAG query endpoint.
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.rag.chain import answer_question

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)) -> ChatResponse:
    result = answer_question(request.question, current_user["role"])
    return ChatResponse(**result)
