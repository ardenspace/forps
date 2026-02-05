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


# ── Members ────────────────────────────────────────────────

@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """워크스페이스 멤버 목록"""
    membership = await workspace_service.get_user_membership(db, workspace_id, user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    return await workspace_service.get_workspace_members(db, workspace_id)


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: UUID,
    data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """멤버 초대 (Owner만)"""
    my_membership = await workspace_service.get_user_membership(db, workspace_id, user.id)
    if not my_membership or my_membership.role != WorkspaceRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can add members")

    member = await workspace_service.add_member(db, workspace_id, data.email, data.role)
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    return member


@router.delete("/{workspace_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: UUID,
    member_user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """멤버 제거 (Owner만)"""
    my_membership = await workspace_service.get_user_membership(db, workspace_id, user.id)
    if not my_membership or my_membership.role != WorkspaceRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can remove members")

    # 자기 자신 제거 방지
    if member_user_id == user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    success = await workspace_service.remove_member(db, workspace_id, member_user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
