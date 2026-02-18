from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Team Schemas
class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class TeamResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None
    agent_count: Optional[int] = None

    class Config:
        from_attributes = True


# Team Member Schemas
class TeamMemberAdd(BaseModel):
    email: str
    role: Optional[str] = "member"  # member, admin, owner


class TeamMemberUpdate(BaseModel):
    role: str  # member, admin, owner


class TeamMemberResponse(BaseModel):
    id: UUID
    team_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
    
    # User details
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    """Extended team response with members and agents"""
    members: List[TeamMemberResponse] = []
    
    class Config:
        from_attributes = True
