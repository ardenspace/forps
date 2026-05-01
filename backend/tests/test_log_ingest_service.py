"""log_ingest_service 단위 테스트.

설계서: 2026-05-01-error-log-phase2-ingest-design.md §3.1
"""

import asyncio
import uuid
from datetime import datetime, timedelta

import bcrypt
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_ingest_token import LogIngestToken
from app.models.workspace import Workspace
from app.models.project import Project
from app.services import log_ingest_service


async def _seed_project_and_token(
    db: AsyncSession,
    *,
    secret: str = "test-secret-256bit",
    revoked: bool = False,
    rate_limit_per_minute: int = 600,
) -> tuple[Project, LogIngestToken, str]:
    """Workspace + Project + LogIngestToken 시드. 반환: (project, token, plain_secret)."""
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.flush()

    secret_hash = bcrypt.hashpw(secret.encode(), bcrypt.gensalt(rounds=4)).decode()
    token = LogIngestToken(
        project_id=proj.id,
        name="test-token",
        secret_hash=secret_hash,
        rate_limit_per_minute=rate_limit_per_minute,
    )
    if revoked:
        token.revoked_at = datetime.utcnow()
    db.add(token)
    await db.commit()
    await db.refresh(proj)
    await db.refresh(token)
    return proj, token, secret


# ---- parse_token ----

async def test_parse_token_no_header():
    """Authorization 헤더 None → 401."""
    with pytest.raises(HTTPException) as exc:
        await log_ingest_service.parse_token(None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token"


async def test_parse_token_no_dot_separator():
    """Bearer 다음에 . 분리자 없음 → 401."""
    with pytest.raises(HTTPException) as exc:
        await log_ingest_service.parse_token("Bearer just-secret-no-dot")
    assert exc.value.status_code == 401


async def test_parse_token_invalid_uuid():
    """key_id 가 UUID 아님 → 401."""
    with pytest.raises(HTTPException) as exc:
        await log_ingest_service.parse_token("Bearer notauuid.somesecret")
    assert exc.value.status_code == 401


async def test_parse_token_valid():
    """Bearer <uuid>.<secret> → (uuid_obj, secret_str)."""
    key_id = uuid.uuid4()
    secret = "the-secret"
    parsed_id, parsed_secret = await log_ingest_service.parse_token(
        f"Bearer {key_id}.{secret}"
    )
    assert parsed_id == key_id
    assert parsed_secret == secret


# ---- verify_token ----

async def test_verify_token_lookup_fail(async_session: AsyncSession):
    """key_id 가 DB 에 없음 → 401."""
    with pytest.raises(HTTPException) as exc:
        await log_ingest_service.verify_token(async_session, uuid.uuid4(), "any-secret")
    assert exc.value.status_code == 401


async def test_verify_token_revoked(async_session: AsyncSession):
    """revoked_at set → 401."""
    proj, token, secret = await _seed_project_and_token(async_session, revoked=True)
    with pytest.raises(HTTPException) as exc:
        await log_ingest_service.verify_token(async_session, token.id, secret)
    assert exc.value.status_code == 401


async def test_verify_token_bcrypt_fail(async_session: AsyncSession):
    """잘못된 secret → 401."""
    proj, token, secret = await _seed_project_and_token(async_session)
    with pytest.raises(HTTPException) as exc:
        await log_ingest_service.verify_token(async_session, token.id, "wrong-secret")
    assert exc.value.status_code == 401


async def test_verify_token_success_and_last_used(async_session: AsyncSession):
    """정상 verify → token 반환 + last_used_at 갱신 (in-memory)."""
    proj, token, secret = await _seed_project_and_token(async_session)
    assert token.last_used_at is None

    verified = await log_ingest_service.verify_token(async_session, token.id, secret)
    assert verified.id == token.id
    assert verified.last_used_at is not None
