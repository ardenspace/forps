from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.workspace import WorkspaceRole


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    my_role: WorkspaceRole
    task_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
