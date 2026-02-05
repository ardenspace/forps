from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.workspace import WorkspaceRole
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceMemberResponse,
    AddMemberRequest,
)
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """내 워크스페이스 목록"""
    return await workspace_service.get_user_workspaces(db, user.id)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
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
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """워크스페이스 상세"""
    workspace = await workspace_service.get_workspace(db, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    # TODO: 멤버 여부 확인
    return workspace
