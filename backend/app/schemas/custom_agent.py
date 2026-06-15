from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re


def validate_cron_expression(cron: str) -> bool:
    """Validate cron expression format (simplified validation)"""
    parts = cron.strip().split()
    if len(parts) != 5:
        return False
    
    # Simple validation - check each part is valid
    ranges = [
        (0, 59),  # minute
        (0, 23),  # hour
        (1, 31),  # day
        (1, 12),  # month
        (0, 6),   # weekday
    ]
    
    for i, part in enumerate(parts):
        if part == '*':
            continue
        if '/' in part:  # Step values like */5
            continue
        if '-' in part:  # Ranges like 1-5
            continue
        if ',' in part:  # Lists like 1,3,5
            continue
        try:
            val = int(part)
            if not (ranges[i][0] <= val <= ranges[i][1]):
                return False
        except ValueError:
            return False
    return True


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
    scheduled_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=128000)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    
    # Tools
    enabled_tools: List[str] = Field(default_factory=list)
    tool_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Scheduling
    trigger: str = Field(default="manual", pattern="^(manual|scheduled)$")
    schedule: Optional[str] = None
    schedule_enabled: bool = Field(default=True)
    
    @field_validator('schedule')
    @classmethod
    def validate_schedule(cls, v, info):
        if v == "":
            return None
        if v is not None:
            if not validate_cron_expression(v):
                raise ValueError('Invalid cron expression format')
        return v
    
    @field_validator('trigger')
    @classmethod
    def validate_trigger_schedule(cls, v, info):
        # Will be checked after all fields are populated
        return v


class CustomAgentCreate(CustomAgentBase):
    team_id: Optional[UUID] = None
    template_id: Optional[UUID] = None
    
    def validate_schedule_required(self):
        """Validate that schedule is provided when trigger is 'scheduled'"""
        if self.trigger == 'scheduled' and not self.schedule:
            raise ValueError('Schedule is required when trigger is set to "scheduled"')
        return self


class CustomAgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    visibility: Optional[str] = Field(None, pattern="^(private|team|public)$")
    category: Optional[str] = None
    
    model_name: Optional[str] = Field(None, min_length=1, max_length=100)
    system_prompt: Optional[str] = Field(None, min_length=1)
    scheduled_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=128000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    enabled_tools: Optional[List[str]] = None
    tool_config: Optional[Dict[str, Any]] = None
    
    # Scheduling
    trigger: Optional[str] = Field(None, pattern="^(manual|scheduled)$")
    schedule: Optional[str] = None
    schedule_enabled: Optional[bool] = None
    
    team_id: Optional[UUID] = None
    
    @field_validator('schedule')
    @classmethod
    def validate_schedule(cls, v):
        if v == "":
            return None
        if v is not None and not validate_cron_expression(v):
            raise ValueError('Invalid cron expression format')
        return v


class CustomAgentResponse(CustomAgentBase):
    id: UUID
    user_id: UUID
    team_id: Optional[UUID]

    is_template: bool
    template_id: Optional[UUID]

    # Scheduling
    last_scheduled_run: Optional[datetime]
    next_scheduled_run: Optional[datetime]
    beat_registered: bool = False

    # Stats (calculated from analytics)
    run_count: int = 0
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
