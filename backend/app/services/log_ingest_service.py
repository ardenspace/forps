"""log-ingest 서비스 — 토큰 검증 / rate limit / batch INSERT.

설계서: 2026-05-01-error-log-phase2-ingest-design.md §3.1
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

import bcrypt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_ingest_token import LogIngestToken

logger = logging.getLogger(__name__)


def _invalid_token() -> HTTPException:
    """timing attack 회피용 통일 401 — 사유 구분 안 함."""
    return HTTPException(status_code=401, detail="Invalid token")


async def parse_token(authorization_header: str | None) -> tuple[UUID, str]:
    """Bearer <key_id>.<secret> → (key_id_uuid, secret).

    형식 깨짐 → 401. key_id UUID parse fail → 401.
    """
    if not authorization_header or not authorization_header.startswith("Bearer "):
        raise _invalid_token()
    raw = authorization_header[len("Bearer "):]
    if "." not in raw:
        raise _invalid_token()
    # key_id 와 secret 분리 — secret 안의 . 도 허용 (key_id 는 UUID 라 . 없음)
    key_id_str, _, secret = raw.partition(".")
    if not secret:
        raise _invalid_token()
    try:
        key_id = UUID(key_id_str)
    except (ValueError, AttributeError):
        raise _invalid_token()
    return key_id, secret


async def verify_token(db: AsyncSession, key_id: UUID, secret: str) -> LogIngestToken:
    """key_id lookup → bcrypt verify → last_used_at 갱신 (in-memory).

    실패 시 401 (사유 구분 안 함). 성공 시 token 반환.
    DB commit 은 caller (ingest_batch) 가 묶음.
    """
    token = await db.get(LogIngestToken, key_id)
    if token is None:
        raise _invalid_token()
    if token.revoked_at is not None:
        raise _invalid_token()

    # bcrypt 동기 — async endpoint 에서 event loop block 회피
    is_valid = await asyncio.to_thread(
        bcrypt.checkpw,
        secret.encode("utf-8"),
        token.secret_hash.encode("utf-8"),
    )
    if not is_valid:
        raise _invalid_token()

    token.last_used_at = datetime.utcnow()
    return token
