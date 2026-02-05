from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.models.workspace import WorkspaceRole
from app.schemas.project import ProjectCreate
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

        # task_count
        count_stmt = select(func.count()).where(Task.project_id == project.id)
        count_result = await db.execute(count_stmt)
        task_count = count_result.scalar()

        project_list.append({
            **project.__dict__,
            "my_role": role,
            "task_count": task_count,
        })

    return project_list


async def get_project(db: AsyncSession, project_id: UUID) -> Project | None:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
