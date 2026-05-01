"""log query API 의 Pydantic schemas.

설계서: 2026-05-01-error-log-phase4-query-design.md §3.2
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ---- Git context refs ----

class HandoffRef(BaseModel):
    """git 컨텍스트의 handoff lookup."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    commit_sha: str
    branch: str
    author_git_login: str
    pushed_at: datetime


class TaskRef(BaseModel):
    """git 컨텍스트의 task lookup. archived 포함."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    external_id: str | None
    title: str
    status: str
    last_commit_sha: str | None
    archived_at: datetime | None


class GitPushEventRef(BaseModel):
    """git 컨텍스트의 push event lookup."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    head_commit_sha: str
    branch: str
    pusher: str
    received_at: datetime


class GitContextBundle(BaseModel):
    handoffs: list[HandoffRef]
    tasks: list[TaskRef]
    git_push_event: GitPushEventRef | None


class GitContextWrapper(BaseModel):
    first_seen: GitContextBundle
    previous_good_sha: str | None


# ---- ErrorGroup ----

class ErrorGroupSummary(BaseModel):
    """GET /errors 목록 항목."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    fingerprint: str
    exception_class: str
    exception_message_sample: str | None
    event_count: int
    status: str  # ErrorGroupStatus enum value
    first_seen_at: datetime
    first_seen_version_sha: str
    last_seen_at: datetime
    last_seen_version_sha: str
    resolved_at: datetime | None = None
    resolved_by_user_id: UUID | None = None
    resolved_in_version_sha: str | None = None


class ErrorGroupListResponse(BaseModel):
    items: list[ErrorGroupSummary]
    total: int


# ---- LogEvent ----

class LogEventSummary(BaseModel):
    """LogEvent 응답 항목 (stack_trace 제외 — 길이 제한)."""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    level: str  # LogLevel enum value
    message: str
    logger_name: str
    version_sha: str
    environment: str
    hostname: str
    emitted_at: datetime
    received_at: datetime
    fingerprint: str | None
    exception_class: str | None
    exception_message: str | None


class LogEventListResponse(BaseModel):
    items: list[LogEventSummary]
    total: int


# ---- 상세 ----

class ErrorGroupDetail(BaseModel):
    group: ErrorGroupSummary
    recent_events: list[LogEventSummary]
    git_context: GitContextWrapper


# ---- PATCH /errors/{id} ----


class ErrorGroupStatusUpdate(BaseModel):
    """PATCH /errors/{id} 요청 body. action 기반 (status 직접 X)."""
    model_config = ConfigDict(extra="forbid")
    action: Literal["resolve", "ignore", "reopen", "unmute"]
    resolved_in_version_sha: str | None = None  # action='resolve' 일 때만 의미.
