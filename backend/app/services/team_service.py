from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from app.models.team import Team, TeamMember
from app.models.user import User
from app.models.custom_agent import CustomAgent
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberAdd
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status


class TeamService:
    """Service for managing teams and team memberships"""

    @staticmethod
    async def create_team(db: AsyncSession, team_data: TeamCreate, user_id: UUID) -> Team:
        """Create a new team"""
        team = Team(
            name=team_data.name,
            description=team_data.description,
            created_by=user_id
        )
        db.add(team)
        await db.commit()
        await db.refresh(team)
        
        # Add creator as owner
        owner_member = TeamMember(
            team_id=team.id,
            user_id=user_id,
            role="owner"
        )
        db.add(owner_member)
        await db.commit()
        await db.refresh(team)
        return team

    @staticmethod
    async def get_user_teams(db: AsyncSession, user_id: UUID) -> List[Team]:
        """Get all teams user is a member of"""
        result = await db.execute(
            select(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .filter(TeamMember.user_id == user_id)
            .options(selectinload(Team.members))
        )
        teams = list(result.scalars().all())
        
        # Add counts
        for team in teams:
            team.member_count = len(team.members)
            agent_count_result = await db.execute(
                select(func.count(CustomAgent.id)).filter(
                    CustomAgent.team_id == team.id
                )
            )
            team.agent_count = agent_count_result.scalar()
        
        return teams

    @staticmethod
    async def get_team(db: AsyncSession, team_id: UUID, user_id: UUID) -> Team:
        """Get team details (must be member)"""
        # Check membership
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this team"
            )
        
        result = await db.execute(
            select(Team)
            .filter(Team.id == team_id)
            .options(selectinload(Team.members))
        )
        team = result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        # Add counts
        team.member_count = len(team.members)
        agent_count_result = await db.execute(
            select(func.count(CustomAgent.id)).filter(
                CustomAgent.team_id == team.id
            )
        )
        team.agent_count = agent_count_result.scalar()
        
        return team

    @staticmethod
    async def add_member(
        db: AsyncSession,
        team_id: UUID,
        member_data: TeamMemberAdd,
        requester_id: UUID
    ) -> TeamMember:
        """Add a member to team (admin/owner only)"""
        # Check if requester is admin/owner
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == requester_id
            )
        )
        requester_member = result.scalar_one_or_none()
        
        if not requester_member or requester_member.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team admins/owners can add members"
            )
        
        # Find user by email
        result = await db.execute(
            select(User).filter(User.email == member_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {member_data.email} not found"
            )
        
        # Check if already member
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user.id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this team"
            )
        
        # Add member
        new_member = TeamMember(
            team_id=team_id,
            user_id=user.id,
            role=member_data.role
        )
        db.add(new_member)
        await db.commit()
        await db.refresh(new_member)
        
        # Attach user details for response
        new_member.user_email = user.email
        new_member.user_name = user.email  # Use email as name for now
        
        return new_member

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        team_id: UUID,
        user_id: UUID,
        requester_id: UUID
    ):
        """Remove member from team (admin/owner only, cannot remove owner)"""
        # Check if requester is admin/owner
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == requester_id
            )
        )
        requester_member = result.scalar_one_or_none()
        
        if not requester_member or requester_member.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team admins/owners can remove members"
            )
        
        # Get member to remove
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Cannot remove owner
        if member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove team owner"
            )
        
        await db.delete(member)
        await db.commit()

    @staticmethod
    async def update_member_role(
        db: AsyncSession,
        team_id: UUID,
        user_id: UUID,
        new_role: str,
        requester_id: UUID
    ) -> TeamMember:
        """Update member role (owner only, cannot change owner role)"""
        # Check if requester is owner
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == requester_id
            )
        )
        requester_member = result.scalar_one_or_none()
        
        if not requester_member or requester_member.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team owner can change roles"
            )
        
        # Get member to update
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Cannot change owner role
        if member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change owner role"
            )
        
        member.role = new_role
        await db.commit()
        await db.refresh(member)
        return member

    @staticmethod
    async def get_team_members(db: AsyncSession, team_id: UUID, user_id: UUID) -> List[TeamMember]:
        """Get all members of a team (must be member to view)"""
        # Check membership
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        is_member = result.scalar_one_or_none()
        
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this team"
            )
        
        result = await db.execute(
            select(TeamMember).filter(TeamMember.team_id == team_id)
        )
        members = list(result.scalars().all())
        
        # Attach user details
        for member in members:
            user_result = await db.execute(
                select(User).filter(User.id == member.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                member.user_email = user.email
                member.user_name = user.email  # Use email as name for now
        
        return members

    @staticmethod
    async def delete_team(db: AsyncSession, team_id: UUID, user_id: UUID):
        """Delete team (owner only)"""
        # Check if user is owner
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
                TeamMember.role == "owner"
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only team owner can delete team"
            )
        
        result = await db.execute(
            select(Team).filter(Team.id == team_id)
        )
        team = result.scalar_one_or_none()
        
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found"
            )
        
        await db.delete(team)
        await db.commit()

    @staticmethod
    async def get_team_agents(db: AsyncSession, team_id: UUID, user_id: UUID) -> List[CustomAgent]:
        """Get all agents shared with team (must be member)"""
        # Check membership
        result = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id
            )
        )
        is_member = result.scalar_one_or_none()
        
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this team"
            )
        
        result = await db.execute(
            select(CustomAgent).filter(CustomAgent.team_id == team_id)
        )
        agents = list(result.scalars().all())
        
        return agents
