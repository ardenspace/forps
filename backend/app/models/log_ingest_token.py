import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LogIngestToken(Base):
    """프로젝트별 로그 수신 토큰.

    설계서: 2026-04-26-error-log-design.md §4.1
    토큰 평문 = "<key_id>.<secret>". key_id == row.id (UUID 문자열).
    secret_hash 는 bcrypt(secret) — 평문은 발급 시 1회만 응답.
    """

    __tablename__ = "log_ingest_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    name: Mapped[str]
    secret_hash: Mapped[str]

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(default=None)
    rate_limit_per_minute: Mapped[int] = mapped_column(default=600)

    def __init__(self, **kwargs: object) -> None:
        kwargs.setdefault("rate_limit_per_minute", 600)
        super().__init__(**kwargs)
