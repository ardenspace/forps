from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.workspace import WorkspaceRole
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services import project_service
from app.services.permission_service import get_effective_role, can_edit

router = APIRouter(tags=["projects"])


@router.get("/workspaces/{workspace_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """워크스페이스의 프로젝트 목록"""
    return await project_service.get_workspace_projects(db, workspace_id, user.id)


@router.post(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    workspace_id: UUID,
    data: ProjectCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """프로젝트 생성 (editor 이상)"""
    # TODO: workspace 멤버 권한 체크
    project = await project_service.create_project(db, workspace_id, user.id, data)
    return {
        **project.__dict__,
        "my_role": WorkspaceRole.OWNER,
        "task_count": 0,
    }


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """프로젝트 상세"""
    project = await project_service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = await get_effective_role(db, user.id, project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Permission denied")

    return {
        **project.__dict__,
        "my_role": role,
        "task_count": 0,  # TODO
    }
