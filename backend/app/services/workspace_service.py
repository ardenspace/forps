from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


async def create_workspace(
    db: AsyncSession, user_id: UUID, data: WorkspaceCreate
) -> Workspace:
    workspace = Workspace(
        name=data.name,
        slug=data.slug,
        description=data.description,
    )
    db.add(workspace)
    await db.flush()

    # 생성자를 Owner로 추가
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user_id,
        role=WorkspaceRole.OWNER,
    )
    db.add(member)
    await db.commit()
    await db.refresh(workspace)

    return workspace


async def get_user_workspaces(db: AsyncSession, user_id: UUID) -> list[dict]:
    """사용자가 속한 워크스페이스 목록 (my_role, member_count 포함)"""
    stmt = (
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember)
        .where(WorkspaceMember.user_id == user_id)
    )
    result = await db.execute(stmt)
    rows = result.all()

    workspaces = []
    for workspace, role in rows:
        # member_count 조회
        count_stmt = select(func.count()).where(
            WorkspaceMember.workspace_id == workspace.id
        )
        count_result = await db.execute(count_stmt)
        member_count = count_result.scalar()

        workspaces.append(
            {
                **workspace.__dict__,
                "my_role": role,
                "member_count": member_count,
            }
        )

    return workspaces


async def get_workspace(db: AsyncSession, workspace_id: UUID) -> Workspace | None:
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_workspace(
    db: AsyncSession,
    workspace: Workspace,
    data: WorkspaceUpdate,
) -> Workspace:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)

    await db.commit()
    await db.refresh(workspace)
    return workspace


async def delete_workspace(db: AsyncSession, workspace: Workspace) -> None:
    await db.delete(workspace)
    await db.commit()


async def get_user_membership(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
) -> WorkspaceMember | None:
    """사용자의 워크스페이스 멤버십 조회 (권한 체크용)"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_workspace_member_count(db: AsyncSession, workspace_id: UUID) -> int:
    count_stmt = select(func.count()).where(
        WorkspaceMember.workspace_id == workspace_id
    )
    count_result = await db.execute(count_stmt)
    return int(count_result.scalar() or 0)
