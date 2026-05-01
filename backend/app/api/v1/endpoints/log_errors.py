"""GET /errors, GET /errors/{group_id} — ErrorGroup 조회.

설계서: 2026-05-01-error-log-phase4-query-design.md §3.3
프로젝트 멤버 권한 (VIEWER 포함).
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_project_member
from app.database import get_db
from app.dependencies import CurrentUser
from app.models.error_group import ErrorGroup, ErrorGroupStatus
from app.models.workspace import WorkspaceRole
from app.schemas.log_query import (
    ErrorGroupDetail,
    ErrorGroupListResponse,
    ErrorGroupStatusUpdate,
    ErrorGroupSummary,
    GitContextBundle,
    GitContextWrapper,
    GitPushEventRef,
    HandoffRef,
    LogEventSummary,
    TaskRef,
)
from app.services import error_group_service, log_query_service

router = APIRouter(prefix="/projects", tags=["log-errors"])


@router.get(
    "/{project_id}/errors",
    response_model=ErrorGroupListResponse,
)
async def list_errors(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    status: ErrorGroupStatus | None = None,
    since: datetime | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    _role: WorkspaceRole = Depends(require_project_member(hide_existence=True)),
):
    """ErrorGroup 목록. 멤버 누구나 (VIEWER 포함)."""
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
    db: AsyncSession = Depends(get_db),
    _role: WorkspaceRole = Depends(require_project_member(hide_existence=True)),
):
    """ErrorGroup 상세 + recent events + git 컨텍스트 + 직전 정상 SHA."""
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


@router.patch(
    "/{project_id}/errors/{group_id}",
    response_model=ErrorGroupSummary,
)
async def patch_error_status(
    project_id: UUID,
    group_id: UUID,
    update: ErrorGroupStatusUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    _role: WorkspaceRole = Depends(require_project_member(
        min_role=WorkspaceRole.OWNER,
        hide_existence=True,
        denied_detail="Owner only",
    )),
):
    """ErrorGroup status 전이 (resolve/ignore/reopen/unmute, OWNER 전용).

    설계서: 2026-04-26-error-log-design.md §4.1 전이 다이어그램.
    """
    group = await db.get(ErrorGroup, group_id)
    if group is None or group.project_id != project_id:
        raise HTTPException(status_code=404, detail="Error group not found")

    try:
        updated = await error_group_service.transition_status(
            db, group,
            action=update.action,
            user_id=user.id,
            resolved_in_version_sha=update.resolved_in_version_sha,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()  # endpoint 가 commit 책임 (service 는 flush 만)
    return ErrorGroupSummary.model_validate(updated)
