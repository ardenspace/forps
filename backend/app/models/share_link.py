import uuid
from datetime import datetime
import enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShareLinkScope(str, enum.Enum):
    PROJECT_READ = "project_read"
    TASK_READ = "task_read"


class ShareLink(Base):
    __tablename__ = "share_links"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    scope: Mapped[ShareLinkScope] = mapped_column(default=ShareLinkScope.PROJECT_READ)

    is_active: Mapped[bool] = mapped_column(default=True)
    expires_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="share_links")
