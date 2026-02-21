from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.workspace import WorkspaceRole
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectMemberResponse,
    AddProjectMemberRequest,
    UpdateProjectMemberRequest,
)
from app.services import project_service, workspace_service
from app.services.permission_service import get_effective_role, can_edit, can_manage

router = APIRouter(tags=["projects"])


@router.get("/workspaces/{workspace_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """워크스페이스의 프로젝트 목록"""
    return await project_service.get_workspace_projects(db, workspace_id, user.id)


@router.get("/projects", response_model=list[ProjectResponse])
async def list_my_projects(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    return await project_service.get_user_projects(db, user.id)


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
    my_membership = await workspace_service.get_user_membership(
        db, workspace_id, user.id
    )
    if not can_edit(my_membership.role if my_membership else None):
        raise HTTPException(status_code=403, detail="Permission denied")

    project = await project_service.create_project(db, workspace_id, user.id, data)
    return {
        **project.__dict__,
        "my_role": WorkspaceRole.OWNER,
        "task_count": 0,
    }


@router.get(
    "/workspaces/{workspace_id}/projects/{project_id}",
    response_model=ProjectResponse,
)
async def get_workspace_project(
    workspace_id: UUID,
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    project = await project_service.get_workspace_project(db, workspace_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = await get_effective_role(db, user.id, project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Permission denied")

    task_count = await project_service.get_project_task_count(db, project_id)
    resp = {**project.__dict__, "my_role": role, "task_count": task_count}
    if role != WorkspaceRole.OWNER:
        resp["discord_webhook_url"] = None
    return resp


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

    task_count = await project_service.get_project_task_count(db, project_id)
    resp = {**project.__dict__, "my_role": role, "task_count": task_count}
    if role != WorkspaceRole.OWNER:
        resp["discord_webhook_url"] = None
    return resp


@router.patch(
    "/workspaces/{workspace_id}/projects/{project_id}",
    response_model=ProjectResponse,
)
async def update_project(
    workspace_id: UUID,
    project_id: UUID,
    data: ProjectUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    project = await project_service.get_workspace_project(db, workspace_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = await get_effective_role(db, user.id, project_id)
    if not can_edit(role):
        raise HTTPException(status_code=403, detail="Permission denied")

    updated_project = await project_service.update_project(db, project, data)
    task_count = await project_service.get_project_task_count(db, project_id)
    resp = {**updated_project.__dict__, "my_role": role, "task_count": task_count}
    if role != WorkspaceRole.OWNER:
        resp["discord_webhook_url"] = None
    return resp


@router.delete(
    "/workspaces/{workspace_id}/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    workspace_id: UUID,
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    project = await project_service.get_workspace_project(db, workspace_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = await get_effective_role(db, user.id, project_id)
    if not can_manage(role):
        raise HTTPException(status_code=403, detail="Permission denied")

    await project_service.delete_project(db, project)


@router.get(
    "/projects/{project_id}/members", response_model=list[ProjectMemberResponse]
)
async def list_project_members(
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    role = await get_effective_role(db, user.id, project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Permission denied")

    return await project_service.get_project_members(db, project_id)


@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: UUID,
    data: AddProjectMemberRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    role = await get_effective_role(db, user.id, project_id)
    if not can_manage(role):
        raise HTTPException(
            status_code=403, detail="Only owner can manage project members"
        )

    target_user = await project_service.get_user_by_email(db, str(data.email))
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    return await project_service.upsert_project_member(
        db, project_id, target_user.id, data.role
    )


@router.patch(
    "/projects/{project_id}/members/{member_user_id}",
    response_model=ProjectMemberResponse,
)
async def update_project_member_role(
    project_id: UUID,
    member_user_id: UUID,
    data: UpdateProjectMemberRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    role = await get_effective_role(db, user.id, project_id)
    if not can_manage(role):
        raise HTTPException(
            status_code=403, detail="Only owner can manage project members"
        )

    member = await project_service.get_project_member(db, project_id, member_user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Project member not found")

    return await project_service.upsert_project_member(
        db, project_id, member_user_id, data.role
    )


@router.delete(
    "/projects/{project_id}/members/{member_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member(
    project_id: UUID,
    member_user_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    role = await get_effective_role(db, user.id, project_id)
    if not can_manage(role):
        raise HTTPException(
            status_code=403, detail="Only owner can manage project members"
        )

    if member_user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    success = await project_service.remove_project_member(
        db, project_id, member_user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Project member not found")
