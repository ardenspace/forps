from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.share_link import ShareLinkScope


class ShareLinkCreate(BaseModel):
    scope: ShareLinkScope = ShareLinkScope.PROJECT_READ


class ShareLinkResponse(BaseModel):
    id: UUID
    project_id: UUID
    created_by: UUID
    token: str
    scope: ShareLinkScope
    is_active: bool
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ShareLinkPublicResponse(BaseModel):
    """공유 링크 접근 시 반환되는 응답"""
    project_name: str
    tasks: list[dict]  # 간단한 태스크 목록
