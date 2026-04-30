"""git-settings endpoint Pydantic 스키마.

설계서: 2026-04-26-ai-task-automation-design.md §5.2
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GitSettingsResponse(BaseModel):
    """GET /git-settings — PAT 평문은 절대 응답에 포함 안 함."""

    model_config = ConfigDict(from_attributes=True)

    git_repo_url: str | None
    git_default_branch: str
    plan_path: str
    handoff_dir: str
    last_synced_commit_sha: str | None
    has_webhook_secret: bool
    has_github_pat: bool
    public_webhook_url: str


class GitSettingsUpdate(BaseModel):
    """PATCH /git-settings — 모든 필드 optional (부분 갱신)."""

    model_config = ConfigDict(extra="forbid")

    git_repo_url: str | None = None
    git_default_branch: str | None = None
    plan_path: str | None = None
    handoff_dir: str | None = None
    github_pat: str | None = Field(default=None, min_length=1)


class WebhookRegisterResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    webhook_id: int
    was_existing: bool
    public_webhook_url: str


class HandoffSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    branch: str
    author_git_login: str
    commit_sha: str
    pushed_at: datetime
    parsed_tasks_count: int = 0


class ReprocessResponse(BaseModel):
    event_id: UUID
    status: str
