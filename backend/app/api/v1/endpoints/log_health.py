"""GET /log-health — unknown SHA 비율 + clock drift + 24h 송신량.

설계서: 2026-04-26-error-log-design.md §7 Health 표.
멤버 누구나 (VIEWER 포함, 운영 투명성).
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_project_member
from app.database import get_db
from app.models.workspace import WorkspaceRole
from app.schemas.log_health import LogHealthResponse
from app.services import log_health_service

router = APIRouter(prefix="/projects", tags=["log-health"])


@router.get(
    "/{project_id}/log-health",
    response_model=LogHealthResponse,
)
async def get_log_health(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    _role: WorkspaceRole = Depends(require_project_member(hide_existence=True)),
):
    """24h 윈도우 LogEvent 헬스 메트릭. 멤버 누구나."""
    metrics = await log_health_service.compute_health(db, project_id=project_id)
    return LogHealthResponse(**metrics)
