from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr
from app.models.workspace import WorkspaceRole


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    discord_webhook_url: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    discord_webhook_url: str | None = None
    my_role: WorkspaceRole
    task_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    role: WorkspaceRole
    created_at: datetime
    user: "UserBrief"

    model_config = {"from_attributes": True}


class AddProjectMemberRequest(BaseModel):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.VIEWER


class UpdateProjectMemberRequest(BaseModel):
    role: WorkspaceRole


from app.schemas.task import UserBrief

ProjectMemberResponse.model_rebuild()
