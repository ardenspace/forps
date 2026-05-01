"""API 레이어 권한 헬퍼.

엔드포인트 전반에서 반복되던 5줄짜리 프로젝트 멤버십 확인 패턴을
FastAPI Depends 한 줄로 대체.
"""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.workspace import WorkspaceRole
from app.services.permission_service import get_effective_role


_ROLE_ORDER = {
    WorkspaceRole.VIEWER: 0,
    WorkspaceRole.EDITOR: 1,
    WorkspaceRole.OWNER: 2,
}


def _meets(role: WorkspaceRole, min_role: WorkspaceRole) -> bool:
    return _ROLE_ORDER[role] >= _ROLE_ORDER[min_role]


async def check_project_member(
    db: AsyncSession,
    user_id: UUID,
    project_id: UUID,
    *,
    min_role: WorkspaceRole = WorkspaceRole.VIEWER,
    hide_existence: bool = False,
    denied_detail: str = "Permission denied",
) -> WorkspaceRole:
    """프로젝트 멤버 + 최소 role 확인.

    함수 호출용 — share_link 처럼 path 에 project_id 가 없고
    리소스 fetch 후에 project_id 가 도출되는 endpoint 에서 사용.

    2단계 정책:
        ① 멤버 아닌 경우 — hide_existence=True 면 404 'Project not found'
           (리소스 존재 자체를 숨김, Phase 4+ 신규 endpoint), 아니면 403.
        ② 멤버지만 min_role 미달 — 항상 403 (이미 멤버라 존재는 알려져 있음).
    """
    role = await get_effective_role(db, user_id, project_id)
    if role is None:
        if hide_existence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=denied_detail,
        )
    if not _meets(role, min_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=denied_detail,
        )
    return role


def require_project_member(
    *,
    min_role: WorkspaceRole = WorkspaceRole.VIEWER,
    hide_existence: bool = False,
    denied_detail: str = "Permission denied",
):
    """FastAPI Depends 헬퍼 — path 의 {project_id} 자동 추출.

    사용:
        role: WorkspaceRole = Depends(require_project_member())
        role: WorkspaceRole = Depends(require_project_member(min_role=WorkspaceRole.EDITOR))
        role: WorkspaceRole = Depends(require_project_member(
            min_role=WorkspaceRole.OWNER, hide_existence=True
        ))
    """
    async def dep(
        project_id: UUID,
        user: CurrentUser,
        db: AsyncSession = Depends(get_db),
    ) -> WorkspaceRole:
        return await check_project_member(
            db,
            user.id,
            project_id,
            min_role=min_role,
            hide_existence=hide_existence,
            denied_detail=denied_detail,
        )

    return dep
