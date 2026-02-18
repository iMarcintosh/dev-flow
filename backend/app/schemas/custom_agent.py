from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# Team Schemas
class TeamMemberBase(BaseModel):
    user_id: UUID
    role: str = "member"


class TeamMemberCreate(TeamMemberBase):
    pass


class TeamMemberResponse(TeamMemberBase):
    id: UUID
    team_id: UUID
    joined_at: datetime
    
    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class TeamResponse(TeamBase):
    id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    
    class Config:
        from_attributes = True


# Custom Agent Schemas
class CustomAgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    visibility: str = Field(default="private", pattern="^(private|team|public)$")
    category: Optional[str] = None
    
    # LLM configuration
    model_name: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=128000)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    
    # Tools
    enabled_tools: List[str] = Field(default_factory=list)
    tool_config: Dict[str, Any] = Field(default_factory=dict)


class CustomAgentCreate(CustomAgentBase):
    team_id: Optional[UUID] = None
    template_id: Optional[UUID] = None


class CustomAgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    visibility: Optional[str] = Field(None, pattern="^(private|team|public)$")
    category: Optional[str] = None
    
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    system_prompt: Optional[str] = Field(None, min_length=1)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    enabled_tools: Optional[List[str]] = None
    tool_config: Optional[Dict[str, Any]] = None
    
    team_id: Optional[UUID] = None


class CustomAgentResponse(CustomAgentBase):
    id: UUID
    user_id: UUID
    team_id: Optional[UUID]
    
    is_template: bool
    template_id: Optional[UUID]
    
    run_count: int
    star_count: int
    install_count: int
    last_used_at: Optional[datetime]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Knowledge File Schemas
class AgentKnowledgeFileBase(BaseModel):
    filename: str
    file_type: str
    file_size: int


class AgentKnowledgeFileCreate(AgentKnowledgeFileBase):
    content_hash: str
    storage_path: str


class AgentKnowledgeFileResponse(AgentKnowledgeFileBase):
    id: UUID
    agent_id: UUID
    content_hash: str
    storage_path: str
    processed: bool
    chunk_count: int
    embedding_model: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# Conversation Schemas
class AgentConversationBase(BaseModel):
    title: Optional[str] = None


class AgentConversationCreate(AgentConversationBase):
    agent_id: UUID
    project_id: Optional[UUID] = None


class AgentConversationResponse(AgentConversationBase):
    id: UUID
    agent_id: UUID
    user_id: UUID
    project_id: Optional[UUID]
    message_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Message Schemas
class AgentMessageBase(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system|tool)$")
    content: str


class AgentMessageCreate(BaseModel):
    conversation_id: UUID
    role: str
    content: str
    message_metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMessageResponse(AgentMessageBase):
    id: UUID
    conversation_id: UUID
    message_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    model_config = {
        "from_attributes": True,
    }


# Agent Template Schema
class AgentTemplate(BaseModel):
    """Represents a built-in agent template."""
    name: str
    category: str
    description: str
    icon: str
    system_prompt: str
    model_name: str
    temperature: float
    enabled_tools: List[str]
    
    class Config:
        from_attributes = True
