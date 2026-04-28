import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Handoff(Base):
    """git push 마다 1행 INSERT — handoff 파일 파싱 결과 보존.

    설계서: 2026-04-26-ai-task-automation-design.md §4.2
    UNIQUE (project_id, commit_sha) — webhook 재전송 멱등성.
    commit_sha 는 40자 hex full (CHECK 제약 alembic 에서).
    """

    __tablename__ = "handoffs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    branch: Mapped[str]
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    author_git_login: Mapped[str]
    commit_sha: Mapped[str]
    pushed_at: Mapped[datetime]

    raw_content: Mapped[str | None] = mapped_column(Text)  # 30일 후 NULL (별도 GC, Phase 후반)
    parsed_tasks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON)
    free_notes: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
