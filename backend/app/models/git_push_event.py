import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GitPushEvent(Base):
    """GitHub webhook payload 의 raw 보존.

    설계서: 2026-04-26-ai-task-automation-design.md §4.2
    UNIQUE (project_id, head_commit_sha) — 멱등성.
    head_commit_sha 40자 hex full (CHECK 제약 alembic).
    commits_truncated == True 면 sync 단계에서 Compare API 호출.
    """

    __tablename__ = "git_push_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    branch: Mapped[str]
    head_commit_sha: Mapped[str]
    # Phase 5a — commits_truncated base 정확화 (webhook payload 의 `before` 필드 보존)
    before_commit_sha: Mapped[str | None] = mapped_column(default=None)
    commits: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    commits_truncated: Mapped[bool] = mapped_column(default=False)
    pusher: Mapped[str]

    received_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
