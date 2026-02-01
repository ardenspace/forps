import uuid
from datetime import datetime
import enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class TaskEventAction(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    COMMENTED = "commented"
    DELETED = "deleted"


class TaskEvent(Base):
    __tablename__ = "task_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    action = Column(SQLEnum(TaskEventAction), nullable=False)
    changes = Column(JSON, nullable=True)  # {"field": "status", "old": "todo", "new": "doing"}

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="events")
    user = relationship("User", back_populates="task_events")
