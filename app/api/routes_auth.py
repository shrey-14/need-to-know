# POST /login -> validates users/users.yaml credentials, returns a JWT.
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.security import USERS, create_access_token, verify_password

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest) -> TokenResponse:
    user = USERS.get(credentials.username)
    if user is None or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token(user["username"], user["role"])
    return TokenResponse(access_token=token)
