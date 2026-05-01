"""GET /errors, GET /errors/{group_id} — ErrorGroup 조회.

설계서: 2026-05-01-error-log-phase4-query-design.md §3.3
프로젝트 멤버 권한 (VIEWER 포함).
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.error_group import ErrorGroupStatus
from app.schemas.log_query import (
    ErrorGroupDetail,
    ErrorGroupListResponse,
    ErrorGroupSummary,
    GitContextBundle,
    GitContextWrapper,
    GitPushEventRef,
    HandoffRef,
    LogEventSummary,
    TaskRef,
)
from app.services import log_query_service, project_service
from app.services.permission_service import get_effective_role

router = APIRouter(prefix="/projects", tags=["log-errors"])


@router.get(
    "/{project_id}/errors",
    response_model=ErrorGroupListResponse,
)
async def list_errors(
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    status: ErrorGroupStatus | None = None,
    since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
):
    """ErrorGroup 목록. 멤버 누구나 (VIEWER 포함)."""
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = await get_effective_role(db, user.id, project_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Project not found")

    rows, total = await log_query_service.list_groups(
        db, project_id=project_id,
        status=status, since=since, offset=offset, limit=limit,
    )
    return ErrorGroupListResponse(
        items=[ErrorGroupSummary.model_validate(r) for r in rows],
        total=total,
    )


@router.get(
    "/{project_id}/errors/{group_id}",
    response_model=ErrorGroupDetail,
)
async def get_error_detail(
    project_id: UUID,
    group_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """ErrorGroup 상세 + recent events + git 컨텍스트 + 직전 정상 SHA."""
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = await get_effective_role(db, user.id, project_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Project not found")

    detail = await log_query_service.get_group_detail(
        db, project_id=project_id, group_id=group_id,
    )
    if detail is None:
        raise HTTPException(status_code=404, detail="Error group not found")

    git_ctx = detail["git_context"]
    return ErrorGroupDetail(
        group=ErrorGroupSummary.model_validate(detail["group"]),
        recent_events=[LogEventSummary.model_validate(e) for e in detail["recent_events"]],
        git_context=GitContextWrapper(
            first_seen=GitContextBundle(
                handoffs=[HandoffRef.model_validate(h) for h in git_ctx["first_seen"]["handoffs"]],
                tasks=[TaskRef.model_validate(t) for t in git_ctx["first_seen"]["tasks"]],
                git_push_event=(
                    GitPushEventRef.model_validate(git_ctx["first_seen"]["git_push_event"])
                    if git_ctx["first_seen"]["git_push_event"] else None
                ),
            ),
            previous_good_sha=git_ctx["previous_good_sha"],
        ),
    )
