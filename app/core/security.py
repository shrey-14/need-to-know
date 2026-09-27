# Password hashing (bcrypt) and JWT issue/verify.
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import yaml
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

USERS_FILE = Path(__file__).resolve().parents[2] / "users" / "users.yaml"


def load_users() -> dict[str, dict]:
    """Load users.yaml once into a dict keyed by username."""
    with open(USERS_FILE) as f:
        data = yaml.safe_load(f)
    return {user["username"]: user for user in data["users"]}


USERS = load_users()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Raises jose.JWTError if the token is invalid or expired."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """FastAPI dependency: decodes the Authorization: Bearer <token> header."""
    try:
        return decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
