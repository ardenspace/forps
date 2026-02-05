from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


async def create_workspace(
    db: AsyncSession,
    user_id: UUID,
    data: WorkspaceCreate
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

        workspaces.append({
            **workspace.__dict__,
            "my_role": role,
            "member_count": member_count,
        })

    return workspaces


async def get_workspace(db: AsyncSession, workspace_id: UUID) -> Workspace | None:
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_membership(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
) -> WorkspaceMember | None:
    """사용자의 워크스페이스 멤버십 조회 (권한 체크용)"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def add_member(
    db: AsyncSession,
    workspace_id: UUID,
    email: str,
    role: WorkspaceRole,
) -> WorkspaceMember | None:
    """이메일로 사용자를 워크스페이스에 초대"""
    # 사용자 조회
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None  # 사용자 없음

    # 이미 멤버인지 확인
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user.id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # 이미 멤버면 role 업데이트
        existing.role = role
        await db.commit()
        await db.refresh(existing, ["user"])
        return existing

    # 새 멤버 추가
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=role,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member, ["user"])
    return member


async def get_workspace_members(
    db: AsyncSession,
    workspace_id: UUID,
) -> list[WorkspaceMember]:
    """워크스페이스 멤버 목록"""
    stmt = (
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .options(selectinload(WorkspaceMember.user))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def remove_member(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
) -> bool:
    """워크스페이스에서 멤버 제거"""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()

    if not member:
        return False

    await db.delete(member)
    await db.commit()
    return True
