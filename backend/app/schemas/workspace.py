from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.workspace import WorkspaceRole


class WorkspaceCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    my_role: WorkspaceRole
    member_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
