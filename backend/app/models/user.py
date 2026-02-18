from sqlalchemy import Boolean, Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
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
    preferred_models = Column(JSON, nullable=True)  # Model preferences per agent
    
    # Encrypted API keys (stored encrypted, decrypted via properties)
    encrypted_anthropic_key = Column(String(512), nullable=True)
    encrypted_openai_key = Column(String(512), nullable=True)
    encrypted_openrouter_key = Column(String(512), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    
    # Custom agent relationships
    created_teams = relationship("Team", back_populates="creator", foreign_keys="Team.created_by")
    team_memberships = relationship("TeamMember", back_populates="user")
    custom_agents = relationship("CustomAgent", back_populates="user")
    agent_conversations = relationship("AgentConversation", back_populates="user")
    
    @property
    def anthropic_api_key(self) -> str | None:
        """Decrypt and return Anthropic API key."""
        if not self.encrypted_anthropic_key:
            return None
        from app.security.encryption import decrypt_api_key
        return decrypt_api_key(self.encrypted_anthropic_key)
    
    @property
    def openai_api_key(self) -> str | None:
        """Decrypt and return OpenAI API key."""
        if not self.encrypted_openai_key:
            return None
        from app.security.encryption import decrypt_api_key
        return decrypt_api_key(self.encrypted_openai_key)
    
    @property
    def openrouter_api_key(self) -> str | None:
        """Decrypt and return OpenRouter API key."""
        if not self.encrypted_openrouter_key:
            return None
        from app.security.encryption import decrypt_api_key
        return decrypt_api_key(self.encrypted_openrouter_key)


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)  # google|github|apple|microsoft
    provider_user_id = Column(String, nullable=False)
    access_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="oauth_accounts")
