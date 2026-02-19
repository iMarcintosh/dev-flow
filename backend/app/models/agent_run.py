from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum
from app.database import Base


class AgentTrigger(str, enum.Enum):
    MANUAL = "manual"
    CHAT = "chat"
    EVENT = "event"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"


class AgentRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String, nullable=False)
    trigger = Column(SQLEnum(AgentTrigger), nullable=False, default=AgentTrigger.MANUAL)
    status = Column(SQLEnum(AgentRunStatus), nullable=False, default=AgentRunStatus.PENDING)
    input = Column(JSON, nullable=True)
    output = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="agent_runs")
    logs = relationship("AgentRunLog", back_populates="agent_run", cascade="all, delete-orphan")


class AgentRunLog(Base):
    __tablename__ = "agent_run_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False)
    level = Column(String, nullable=False, default="info")  # info|warning|error
    message = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))

    agent_run = relationship("AgentRun", back_populates="logs")
