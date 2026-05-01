from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.task import TaskSource, TaskStatus


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
    due_date: date | None = None
    assignee_id: UUID | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    due_date: date | None = None
    assignee_id: UUID | None = None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    due_date: date | None
    assignee_id: UUID | None
    reporter_id: UUID | None
    created_at: datetime
    updated_at: datetime
    assignee: UserBrief | None = None
    reporter: UserBrief | None = None
    # Phase 5b — frontend 가 source 배지 / git 연동 정보 표시 (Phase 1 모델 누락분 노출)
    source: TaskSource = TaskSource.MANUAL
    external_id: str | None = None
    last_commit_sha: str | None = None
    archived_at: datetime | None = None
    # Phase 5 follow-up B2 — handoff missing 배지 (TaskCard ⚠️)
    handoff_missing: bool = False

    model_config = {"from_attributes": True}


class TaskFilters(BaseModel):
    status: TaskStatus | None = None
    assignee_id: UUID | None = None
    mine_only: bool = False


