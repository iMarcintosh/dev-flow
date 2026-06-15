from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.database import Base
from pgvector.sqlalchemy import Vector


class ItemType(str, enum.Enum):
    EPIC = "epic"
    STORY = "story"
    BUG = "bug"
    TASK = "task"
    SPIKE = "spike"


class ItemStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class ItemPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    type = Column(SQLEnum(ItemType), nullable=False, default=ItemType.TASK)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    status = Column(SQLEnum(ItemStatus), nullable=False, default=ItemStatus.BACKLOG)
    priority = Column(SQLEnum(ItemPriority), nullable=False, default=ItemPriority.MEDIUM)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_agent_id = Column(UUID(as_uuid=True), ForeignKey("custom_agents.id", ondelete="SET NULL"), nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=True)
    tags = Column(JSON, default=list)
    position = Column(Float, nullable=False, default=0.0)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    project = relationship("Project", back_populates="items")
    assignee = relationship("User", foreign_keys=[assignee_id])
    assigned_agent = relationship("CustomAgent", foreign_keys=[assigned_agent_id])
    creator = relationship("User", foreign_keys=[created_by])
    parent = relationship("Item", remote_side=[id], backref="subtasks")

