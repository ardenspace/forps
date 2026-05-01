"""log-tokens API 의 Pydantic schemas.

설계서: 2026-05-01-error-log-phase2-ingest-design.md §3.5
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LogTokenCreate(BaseModel):
    """POST /log-tokens 요청 — name 필수, rate_limit 선택."""
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    rate_limit_per_minute: int | None = Field(default=None, ge=1, le=10000)


class LogTokenResponse(BaseModel):
    """POST /log-tokens 응답 — token 평문 1회 노출 (이후 secret_hash 만)."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    token: str  # 평문 <key_id>.<secret> — 응답 1회만
    rate_limit_per_minute: int
    created_at: datetime


class LogTokenRevokedResponse(BaseModel):
    """DELETE /log-tokens/{id} 응답."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    revoked_at: datetime


class LogTokenSummary(BaseModel):
    """GET /log-tokens 목록 항목. **secret 은 절대 노출 금지** (response_model 로 컴파일 시 보장)."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    rate_limit_per_minute: int
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class LogTokenListResponse(BaseModel):
    items: list[LogTokenSummary]
