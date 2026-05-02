import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# `@username` 멘션 매핑용 — parser 의 `[A-Za-z0-9_-]+` 와 호환되도록 lowercase 만 허용
USERNAME_PATTERN = r"^[a-z0-9_-]{2,32}$"


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str | None = None
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """PATCH /auth/me — 본인 프로필 부분 수정. 현재는 username 만 지원."""
    username: str | None = Field(default=None, pattern=USERNAME_PATTERN)


class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserResponse
