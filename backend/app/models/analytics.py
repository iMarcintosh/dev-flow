"""
Analytics Models for tracking usage metrics.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base


class AgentAnalytics(Base):
    """
    Aggregated analytics for custom agents.
    Tracks usage, performance, and tool metrics.
    """
    __tablename__ = "agent_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("custom_agents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Time period
    date = Column(TIMESTAMP(timezone=True), nullable=False)  # Aggregated by day
    
    # Usage metrics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time = Column(Float, nullable=True)  # in seconds
    min_response_time = Column(Float, nullable=True)
    max_response_time = Column(Float, nullable=True)
    total_response_time = Column(Float, default=0)
    
    # Token usage (if available from LLM)
    total_tokens = Column(Integer, default=0)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    
    # Tool usage
    tool_calls_count = Column(Integer, default=0)
    
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("CustomAgent", backref="analytics")
    user = relationship("User", backref="agent_analytics")


class ToolUsageLog(Base):
    """
    Logs individual tool usage for analytics.
    """
    __tablename__ = "tool_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("custom_agents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    tool_name = Column(String, nullable=False)
    execution_time = Column(Float, nullable=True)  # in seconds
    success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)
    
    timestamp = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    agent = relationship("CustomAgent")
    user = relationship("User")
