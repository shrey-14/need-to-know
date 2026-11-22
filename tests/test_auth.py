"""Authentication: who gets a token, what role it carries, and who is refused.

Never reaches the LLM: every /chat call here is rejected before the RAG chain.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.main import app

client = TestClient(app)

# Demo accounts (plaintext passwords are documented in users/users.yaml).
DEMO = {
    "finance_user": ("finance123", "finance"),
    "marketing_user": ("marketing123", "marketing"),
    "hr_user": ("hr123", "hr"),
    "engineering_user": ("engineering123", "engineering"),
    "employee_user": ("employee123", "employee"),
    "clevel_user": ("clevel123", "c_level"),
}


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("username", sorted(DEMO))
def test_login_issues_token_with_the_users_role(username: str) -> None:
    password, role = DEMO[username]
    res = client.post("/login", json={"username": username, "password": password})
    assert res.status_code == 200
    claims = decode_access_token(res.json()["access_token"])
    assert claims["sub"] == username
    assert claims["role"] == role


@pytest.mark.parametrize(
    "username,password",
    [("finance_user", "wrong"), ("nobody", "finance123"), ("finance_user", "")],
)
def test_bad_credentials_are_rejected(username: str, password: str) -> None:
    res = client.post("/login", json={"username": username, "password": password})
    assert res.status_code == 401


def test_chat_requires_a_token() -> None:
    assert client.post("/chat", json={"question": "hi"}).status_code == 401


def test_chat_rejects_a_forged_token() -> None:
    forged = jwt.encode(
        {"sub": "x", "role": "c_level", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "not-the-real-secret",
        algorithm="HS256",
    )
    res = client.post("/chat", json={"question": "hi"}, headers={"Authorization": f"Bearer {forged}"})
    assert res.status_code == 401


def test_chat_rejects_an_expired_token() -> None:
    settings = get_settings()
    expired = jwt.encode(
        {"sub": "finance_user", "role": "finance", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    res = client.post("/chat", json={"question": "hi"}, headers={"Authorization": f"Bearer {expired}"})
    assert res.status_code == 401
