from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.task import TaskStatus


class UserBrief(BaseModel):
    id: UUID
    name: str
    email: str

    model_config = {"from_attributes": True}


# ── Task ──────────────────────────────────────────────

class TaskBase(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    due_date: datetime | None = None
    assignee_id: UUID | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None
    assignee_id: UUID | None = None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    due_date: datetime | None
    assignee_id: UUID | None
    reporter_id: UUID | None
    created_at: datetime
    updated_at: datetime
    assignee: UserBrief | None = None
    reporter: UserBrief | None = None

    model_config = {"from_attributes": True}


class TaskFilters(BaseModel):
    status: TaskStatus | None = None
    assignee_id: UUID | None = None
    mine_only: bool = False


