from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import WorkspaceRole
from app.models.project import ProjectMember


async def get_effective_role(
    db: AsyncSession, user_id: UUID, project_id: UUID
) -> WorkspaceRole | None:
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
    )
    result = await db.execute(stmt)
    project_member = result.scalar_one_or_none()

    if project_member:
        return project_member.role

    return None


def can_edit(role: WorkspaceRole | None) -> bool:
    """Editor 이상만 편집 가능"""
    return role in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR)


def can_manage(role: WorkspaceRole | None) -> bool:
    """Owner만 관리 가능 (멤버 관리, 삭제, 공유 링크)"""
    return role == WorkspaceRole.OWNER
