import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LogLevel(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEvent(Base):
    """수신한 로그 한 줄.

    설계서: 2026-04-26-error-log-design.md §4.1
    PostgreSQL declarative range partition by received_at — Task 11 alembic raw SQL.
    SQLAlchemy 측은 일반 테이블처럼 매핑 (parent table).
    version_sha 는 40자 hex full 또는 'unknown' (CHECK 제약 alembic).
    fingerprint / fingerprinted_at 은 ERROR↑ 이벤트만 BackgroundTask 가 채움.

    DDL 측 실제 PK 는 (id, received_at) — PostgreSQL partition key 가 PK 에
    포함되어야 함. ORM 측은 id 단일 PK 로 매핑 (UUID 라 lookup 가능),
    Session.get(LogEvent, uuid) 는 cross-partition scan 발생 — 성능 필요 시
    received_at 명시 필터 사용.
    """

    __tablename__ = "log_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    level: Mapped[LogLevel]
    message: Mapped[str] = mapped_column(Text)
    logger_name: Mapped[str]
    version_sha: Mapped[str]
    environment: Mapped[str]
    hostname: Mapped[str]

    emitted_at: Mapped[datetime]
    received_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # 에러 전용
    exception_class: Mapped[str | None] = mapped_column(default=None)
    exception_message: Mapped[str | None] = mapped_column(Text, default=None)
    stack_trace: Mapped[str | None] = mapped_column(Text, default=None)
    stack_frames: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=None)
    fingerprint: Mapped[str | None] = mapped_column(default=None)
    fingerprinted_at: Mapped[datetime | None] = mapped_column(default=None)

    # 선택
    user_id_external: Mapped[str | None] = mapped_column(default=None)
    request_id: Mapped[str | None] = mapped_column(default=None)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
