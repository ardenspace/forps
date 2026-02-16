from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.schemas.share_link import (
    ShareLinkCreate,
    ShareLinkResponse,
    ShareLinkPublicResponse,
)
from app.services import share_link_service
from app.services.permission_service import get_effective_role, can_manage

router = APIRouter(tags=["share-links"])


@router.post(
    "/projects/{project_id}/share-links",
    response_model=ShareLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_share_link(
    project_id: UUID,
    data: ShareLinkCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """공유 링크 생성 (Owner만)"""
    role = await get_effective_role(db, user.id, project_id)
    if not can_manage(role):
        raise HTTPException(status_code=403, detail="Only owner can create share links")

    return await share_link_service.create_share_link(
        db, project_id, user.id, data.scope
    )


@router.get(
    "/projects/{project_id}/share-links", response_model=list[ShareLinkResponse]
)
async def list_share_links(
    project_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """프로젝트의 공유 링크 목록 (Owner만)"""
    role = await get_effective_role(db, user.id, project_id)
    if not can_manage(role):
        raise HTTPException(status_code=403, detail="Only owner can view share links")

    return await share_link_service.get_project_share_links(db, project_id)


@router.patch(
    "/share-links/{share_link_id}/deactivate", response_model=ShareLinkResponse
)
async def deactivate_share_link(
    share_link_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """공유 링크 비활성화 (Owner만)"""
    share_link = await share_link_service.get_share_link_by_id(db, share_link_id)
    if not share_link:
        raise HTTPException(status_code=404, detail="Share link not found")

    role = await get_effective_role(db, user.id, share_link.project_id)
    if not can_manage(role):
        raise HTTPException(
            status_code=403, detail="Only owner can deactivate share links"
        )

    success = await share_link_service.deactivate_share_link(db, share_link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Share link not found")

    updated = await share_link_service.get_share_link_by_id(db, share_link_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Share link not found")
    return updated


@router.patch("/share-links/{share_link_id}/activate", response_model=ShareLinkResponse)
async def activate_share_link(
    share_link_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    share_link = await share_link_service.get_share_link_by_id(db, share_link_id)
    if not share_link:
        raise HTTPException(status_code=404, detail="Share link not found")

    role = await get_effective_role(db, user.id, share_link.project_id)
    if not can_manage(role):
        raise HTTPException(
            status_code=403, detail="Only owner can activate share links"
        )

    updated = await share_link_service.activate_share_link(db, share_link_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Share link not found")
    return updated


@router.delete("/share-links/{share_link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share_link(
    share_link_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    share_link = await share_link_service.get_share_link_by_id(db, share_link_id)
    if not share_link:
        raise HTTPException(status_code=404, detail="Share link not found")

    role = await get_effective_role(db, user.id, share_link.project_id)
    if not can_manage(role):
        raise HTTPException(status_code=403, detail="Only owner can delete share links")

    success = await share_link_service.delete_share_link(db, share_link_id)
    if not success:
        raise HTTPException(status_code=404, detail="Share link not found")


# 공개 API (인증 불필요)
@router.get("/share/{token}", response_model=ShareLinkPublicResponse)
async def get_shared_project(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """공유 링크를 통한 프로젝트 조회 (인증 불필요)"""
    share_link = await share_link_service.get_share_link_by_token(db, token)
    if not share_link:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    return await share_link_service.get_shared_project_data(db, share_link)
