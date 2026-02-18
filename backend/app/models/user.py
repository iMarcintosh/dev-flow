from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)  # google|github|apple|microsoft
    provider_user_id = Column(String, nullable=False)
    access_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="oauth_accounts")
