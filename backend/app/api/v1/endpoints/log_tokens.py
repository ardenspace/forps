"""log-tokens API endpoints — OWNER 전용 토큰 발급/폐기.

설계서: 2026-05-01-error-log-phase2-ingest-design.md §3.3, §3.4
"""

import secrets
from datetime import datetime
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_project_member
from app.database import get_db
from app.models.log_ingest_token import LogIngestToken
from app.models.workspace import WorkspaceRole
from app.schemas.log_token import (
    LogTokenCreate,
    LogTokenResponse,
    LogTokenRevokedResponse,
)


router = APIRouter(prefix="/projects", tags=["log-tokens"])


@router.post(
    "/{project_id}/log-tokens",
    response_model=LogTokenResponse,
    status_code=201,
)
async def create_log_token(
    project_id: UUID,
    data: LogTokenCreate,
    db: AsyncSession = Depends(get_db),
    _role: WorkspaceRole = Depends(require_project_member(
        min_role=WorkspaceRole.OWNER,
        hide_existence=True,
        denied_detail="Owner only",
    )),
):
    """토큰 발급 — 응답에 평문 token 1회만, DB 에는 bcrypt(secret) 만."""
    # 256-bit secret + bcrypt cost 12
    secret = secrets.token_urlsafe(32)
    secret_hash = bcrypt.hashpw(
        secret.encode("utf-8"), bcrypt.gensalt(rounds=12),
    ).decode("utf-8")

    token = LogIngestToken(
        project_id=project_id,
        name=data.name,
        secret_hash=secret_hash,
        rate_limit_per_minute=data.rate_limit_per_minute or 600,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)

    return LogTokenResponse(
        id=token.id,
        name=token.name,
        token=f"{token.id}.{secret}",  # 평문 — 응답 1회만
        rate_limit_per_minute=token.rate_limit_per_minute,
        created_at=token.created_at,
    )


@router.delete(
    "/{project_id}/log-tokens/{token_id}",
    response_model=LogTokenRevokedResponse,
)
async def revoke_log_token(
    project_id: UUID,
    token_id: UUID,
    db: AsyncSession = Depends(get_db),
    _role: WorkspaceRole = Depends(require_project_member(
        min_role=WorkspaceRole.OWNER,
        hide_existence=True,
        denied_detail="Owner only",
    )),
):
    """토큰 폐기 — soft delete (revoked_at = now)."""
    token = await db.get(LogIngestToken, token_id)
    if token is None or token.project_id != project_id:
        raise HTTPException(status_code=404, detail="Token not found")
    if token.revoked_at is not None:
        raise HTTPException(status_code=400, detail="Token already revoked")

    token.revoked_at = datetime.utcnow()
    await db.commit()
    await db.refresh(token)

    return LogTokenRevokedResponse(id=token.id, revoked_at=token.revoked_at)
