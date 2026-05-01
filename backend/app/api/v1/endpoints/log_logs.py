"""GET /logs — LogEvent raw 조회 + pg_trgm 풀텍스트.

설계서: 2026-05-01-error-log-phase4-query-design.md §3.3
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_project_member
from app.database import get_db
from app.models.log_event import LogLevel
from app.models.workspace import WorkspaceRole
from app.schemas.log_query import LogEventListResponse, LogEventSummary
from app.services import log_query_service

router = APIRouter(prefix="/projects", tags=["log-logs"])


@router.get(
    "/{project_id}/logs",
    response_model=LogEventListResponse,
)
async def list_logs(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    level: LogLevel | None = None,
    since: datetime | None = None,
    q: str | None = Query(default=None, min_length=2, max_length=200),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    _role: WorkspaceRole = Depends(require_project_member(hide_existence=True)),
):
    """LogEvent 목록. q (풀텍스트) 사용 시 자동 level >= WARNING 필터."""
    rows, total = await log_query_service.list_logs(
        db, project_id=project_id,
        level=level, since=since, q=q, offset=offset, limit=limit,
    )
    return LogEventListResponse(
        items=[LogEventSummary.model_validate(r) for r in rows],
        total=total,
    )
