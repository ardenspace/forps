import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ErrorGroupStatus(str, enum.Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"
    REGRESSED = "regressed"


class ErrorGroup(Base):
    """fingerprint 별 에러 집계 (롤업 캐시).

    설계서: 2026-04-26-error-log-design.md §4.1
    UNIQUE (project_id, fingerprint).
    *_version_sha 는 40자 hex full 또는 'unknown' (CHECK 제약 alembic).
    """

    __tablename__ = "error_groups"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    fingerprint: Mapped[str]
    exception_class: Mapped[str]
    exception_message_sample: Mapped[str | None] = mapped_column(Text)

    first_seen_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    first_seen_version_sha: Mapped[str]
    last_seen_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_seen_version_sha: Mapped[str]

    event_count: Mapped[int] = mapped_column(BigInteger, default=0)
    status: Mapped[ErrorGroupStatus] = mapped_column(default=ErrorGroupStatus.OPEN)

    resolved_at: Mapped[datetime | None] = mapped_column(default=None)
    resolved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    resolved_in_version_sha: Mapped[str | None] = mapped_column(default=None)

    last_alerted_new_at: Mapped[datetime | None] = mapped_column(default=None)
    last_alerted_spike_at: Mapped[datetime | None] = mapped_column(default=None)
    last_alerted_regression_at: Mapped[datetime | None] = mapped_column(default=None)

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("status", ErrorGroupStatus.OPEN)
        kwargs.setdefault("event_count", 0)
        super().__init__(**kwargs)
