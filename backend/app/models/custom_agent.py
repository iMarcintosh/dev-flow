from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class CustomAgent(Base):
    __tablename__ = "custom_agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji or icon name
    visibility = Column(String(20), nullable=False, server_default='private')  # 'private', 'team', 'public'
    
    # Template metadata
    is_template = Column(Boolean, nullable=False, server_default='false')
    template_id = Column(UUID(as_uuid=True), ForeignKey('custom_agents.id', ondelete='SET NULL'), nullable=True)
    category = Column(String(50), nullable=True)  # 'code_review', 'testing', 'documentation', etc.
    
    # LLM configuration
    model_name = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=False)
    scheduled_prompt = Column(Text, nullable=True)  # Prompt used for scheduled runs
    temperature = Column(Float, nullable=False, server_default='0.7')
    max_tokens = Column(Integer, nullable=False, server_default='4096')
    top_p = Column(Float, nullable=False, server_default='1.0')
    
    # Tools & capabilities
    enabled_tools = Column(JSONB, nullable=False, server_default='[]')
    tool_config = Column(JSONB, nullable=False, server_default='{}')
    
    # Scheduling
    trigger = Column(String(20), nullable=False, server_default='manual')  # 'manual', 'scheduled'
    schedule = Column(String(100), nullable=True)  # Cron format: "0 9 * * *"
    schedule_enabled = Column(Boolean, nullable=False, server_default='true')
    last_scheduled_run = Column(TIMESTAMP(timezone=True), nullable=True)
    next_scheduled_run = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Stats
    star_count = Column(Integer, nullable=False, server_default='0')  # For marketplace
    install_count = Column(Integer, nullable=False, server_default='0')  # For marketplace
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="custom_agents")
    team = relationship("Team", back_populates="agents")
    template = relationship("CustomAgent", remote_side=[id], foreign_keys=[template_id])
    knowledge_files = relationship("AgentKnowledgeFile", back_populates="agent", cascade="all, delete-orphan")
    conversations = relationship("AgentConversation", back_populates="agent", cascade="all, delete-orphan")


class AgentKnowledgeFile(Base):
    __tablename__ = "agent_knowledge_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('custom_agents.id', ondelete='CASCADE'), nullable=False)
    
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'pdf', 'markdown', 'code', 'text'
    file_size = Column(Integer, nullable=False)  # bytes
    content_hash = Column(String(64), nullable=False)  # SHA256 hash
    storage_path = Column(String(512), nullable=False)  # Path in storage
    
    # Processing status
    processed = Column(Boolean, nullable=False, server_default='false')
    chunk_count = Column(Integer, nullable=False, server_default='0')
    embedding_model = Column(String(100), nullable=True)
    
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    agent = relationship("CustomAgent", back_populates="knowledge_files")


class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('custom_agents.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    
    title = Column(String(255), nullable=True)  # Auto-generated from first message
    message_count = Column(Integer, nullable=False, server_default='0')
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    agent = relationship("CustomAgent", back_populates="conversations")
    user = relationship("User", back_populates="agent_conversations")
    project = relationship("Project")
    messages = relationship("AgentMessage", back_populates="conversation", cascade="all, delete-orphan")


class AgentMessage(Base):
    __tablename__ = "agent_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('agent_conversations.id', ondelete='CASCADE'), nullable=False)
    
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system', 'tool'
    content = Column(Text, nullable=False)
    message_metadata = Column(JSONB, nullable=False, server_default='{}')  # Tool calls, citations, etc.
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("AgentConversation", back_populates="messages")
