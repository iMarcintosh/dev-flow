from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamMemberAdd,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamDetailResponse
)
from app.schemas.custom_agent import CustomAgentResponse
from app.services.team_service import TeamService

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=List[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all teams user is a member of"""
    teams = await TeamService.get_user_teams(db, current_user.id)
    return teams


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new team"""
    team = await TeamService.create_team(db, team_data, current_user.id)
    
    # Add counts for response
    team.member_count = 1  # Creator
    team.agent_count = 0
    
    return team


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team details"""
    team = await TeamService.get_team(db, team_id, current_user.id)
    
    # Get members with details
    members = await TeamService.get_team_members(db, team_id, current_user.id)
    team.members = members
    
    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete team (owner only)"""
    await TeamService.delete_team(db, team_id, current_user.id)
    return None


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def list_team_members(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all members of a team"""
    members = await TeamService.get_team_members(db, team_id, current_user.id)
    return members


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: UUID,
    member_data: TeamMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a member to team (admin/owner only)"""
    member = await TeamService.add_member(db, team_id, member_data, current_user.id)
    return member


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: UUID,
    user_id: UUID,
    role_data: TeamMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update member role (owner only)"""
    member = await TeamService.update_member_role(
        db, team_id, user_id, role_data.role, current_user.id
    )
    return member


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove member from team (admin/owner only)"""
    await TeamService.remove_member(db, team_id, user_id, current_user.id)
    return None


@router.get("/{team_id}/agents", response_model=List[CustomAgentResponse])
async def list_team_agents(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all agents shared with team"""
    agents = await TeamService.get_team_agents(db, team_id, current_user.id)
    return agents
