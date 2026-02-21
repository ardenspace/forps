from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.permission_service import get_effective_role


async def create_project(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
    data: ProjectCreate,
) -> Project:
    project = Project(
        workspace_id=workspace_id,
        name=data.name,
        description=data.description,
    )
    db.add(project)
    await db.flush()

    # 생성자를 Project Owner로 추가
    member = ProjectMember(
        project_id=project.id,
        user_id=user_id,
        role=WorkspaceRole.OWNER,
    )
    db.add(member)

    await db.commit()
    await db.refresh(project)
    return project


async def get_workspace_projects(
    db: AsyncSession,
    workspace_id: UUID,
    user_id: UUID,
) -> list[dict]:
    """워크스페이스의 프로젝트 목록"""
    stmt = select(Project).where(Project.workspace_id == workspace_id)
    result = await db.execute(stmt)
    projects = result.scalars().all()

    project_list = []
    for project in projects:
        role = await get_effective_role(db, user_id, project.id)
        if not role:
            continue

        # task_count
        count_stmt = select(func.count()).where(Task.project_id == project.id)
        count_result = await db.execute(count_stmt)
        task_count = count_result.scalar()

        project_list.append(
            {
                **project.__dict__,
                "my_role": role,
                "task_count": task_count,
            }
        )

    return project_list


async def get_user_projects(
    db: AsyncSession,
    user_id: UUID,
) -> list[dict]:
    stmt = (
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user_id)
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()

    project_list = []
    for project in projects:
        role = await get_effective_role(db, user_id, project.id)
        if not role:
            continue

        count_stmt = select(func.count()).where(Task.project_id == project.id)
        count_result = await db.execute(count_stmt)
        task_count = count_result.scalar()

        project_list.append(
            {
                **project.__dict__,
                "my_role": role,
                "task_count": task_count,
            }
        )

    return project_list


async def get_project(db: AsyncSession, project_id: UUID) -> Project | None:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_workspace_project(
    db: AsyncSession,
    workspace_id: UUID,
    project_id: UUID,
) -> Project | None:
    stmt = select(Project).where(
        Project.workspace_id == workspace_id,
        Project.id == project_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_project(
    db: AsyncSession, project: Project, data: ProjectUpdate
) -> Project:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    await db.delete(project)
    await db.commit()


async def get_project_task_count(db: AsyncSession, project_id: UUID) -> int:
    stmt = select(func.count()).where(Task.project_id == project_id)
    result = await db.execute(stmt)
    return int(result.scalar() or 0)


async def get_project_members(
    db: AsyncSession, project_id: UUID
) -> list[ProjectMember]:
    stmt = (
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .options(selectinload(ProjectMember.user))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_project_member(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
) -> ProjectMember | None:
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def upsert_project_member(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    role: WorkspaceRole,
) -> ProjectMember:
    member = await get_project_member(db, project_id, user_id)
    if member:
        member.role = role
    else:
        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
        )
        db.add(member)

    await db.commit()
    await db.refresh(member, ["user"])
    return member


async def get_user(db: AsyncSession, user_id: UUID) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def remove_project_member(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
) -> bool:
    member = await get_project_member(db, project_id, user_id)
    if not member:
        return False

    await db.delete(member)
    await db.commit()
    return True
