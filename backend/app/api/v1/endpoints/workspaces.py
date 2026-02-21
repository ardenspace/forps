from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.workspace import WorkspaceRole
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
)
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """내 워크스페이스 목록"""
    return await workspace_service.get_user_workspaces(db, user.id)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """워크스페이스 생성"""
    workspace = await workspace_service.create_workspace(db, user.id, data)
    return {
        **workspace.__dict__,
        "my_role": WorkspaceRole.OWNER,
        "member_count": 1,
    }


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """워크스페이스 상세"""
    workspace = await workspace_service.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    membership = await workspace_service.get_user_membership(db, workspace_id, user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    member_count = await workspace_service.get_workspace_member_count(db, workspace_id)
    return {**workspace.__dict__, "my_role": membership.role, "member_count": member_count}


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    workspace = await workspace_service.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    membership = await workspace_service.get_user_membership(db, workspace_id, user.id)
    if not membership or membership.role != WorkspaceRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can update workspace")

    updated_workspace = await workspace_service.update_workspace(db, workspace, data)
    member_count = await workspace_service.get_workspace_member_count(db, workspace_id)
    return {
        **updated_workspace.__dict__,
        "my_role": membership.role,
        "member_count": member_count,
    }


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    workspace = await workspace_service.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    membership = await workspace_service.get_user_membership(db, workspace_id, user.id)
    if not membership or membership.role != WorkspaceRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can delete workspace")

    await workspace_service.delete_workspace(db, workspace)
