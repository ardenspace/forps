import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RateLimitWindow(Base):
    """분당 카운터 — log-ingest 의 PostgreSQL UPSERT 기반 rate limit.

    설계서: 2026-04-26-error-log-design.md §4.1
    PRIMARY KEY (project_id, token_id, window_start) — 분 단위 truncate.
    24시간 지난 row 는 별도 cron 으로 GC (Phase 7).
    """

    __tablename__ = "rate_limit_windows"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    token_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("log_ingest_tokens.id", ondelete="CASCADE"), primary_key=True
    )
    window_start: Mapped[datetime] = mapped_column(primary_key=True)
    event_count: Mapped[int] = mapped_column(default=0)
