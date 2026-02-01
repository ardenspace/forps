import uuid
from datetime import datetime
import enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ShareLinkScope(str, enum.Enum):
    PROJECT_READ = "project_read"  # 프로젝트 전체 읽기
    TASK_READ = "task_read"  # 특정 태스크만 읽기


class ShareLink(Base):
    __tablename__ = "share_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    token = Column(String, unique=True, nullable=False, index=True)
    scope = Column(SQLEnum(ShareLinkScope), nullable=False, default=ShareLinkScope.PROJECT_READ)

    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="share_links")
