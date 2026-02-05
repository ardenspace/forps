from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import WorkspaceRole, WorkspaceMember
from app.models.project import Project, ProjectMember


async def get_effective_role(
    db: AsyncSession,
    user_id: UUID,
    project_id: UUID
) -> WorkspaceRole | None:
    """
    사용자의 프로젝트에 대한 실효 권한을 반환한다.
    1. ProjectMember에 있으면 그 role 반환
    2. 없으면 WorkspaceMember role 상속
    3. 둘 다 없으면 None
    """
    # 1. Project 레벨 확인
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    )
    result = await db.execute(stmt)
    project_member = result.scalar_one_or_none()

    if project_member:
        return project_member.role

    # 2. Workspace 레벨 상속
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        return None

    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == project.workspace_id,
        WorkspaceMember.user_id == user_id
    )
    result = await db.execute(stmt)
    workspace_member = result.scalar_one_or_none()

    if workspace_member:
        return workspace_member.role

    return None


def can_edit(role: WorkspaceRole | None) -> bool:
    """Editor 이상만 편집 가능"""
    return role in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR)


def can_manage(role: WorkspaceRole | None) -> bool:
    """Owner만 관리 가능 (멤버 관리, 삭제, 공유 링크)"""
    return role == WorkspaceRole.OWNER
