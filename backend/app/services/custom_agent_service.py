"""
Service layer for Custom Agent management.

Handles CRUD operations, validation, and business logic for custom agents.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.custom_agent import CustomAgent, AgentKnowledgeFile
from app.models.team import Team, TeamMember
from app.schemas.custom_agent import (
    CustomAgentCreate,
    CustomAgentUpdate,
    CustomAgentResponse,
)


async def create_agent(
    db: AsyncSession,
    user_id: UUID,
    agent_data: CustomAgentCreate
) -> CustomAgent:
    """
    Create a new custom agent.
    
    Args:
        db: Database session
        user_id: ID of user creating the agent
        agent_data: Agent configuration
    
    Returns:
        Created CustomAgent
    """
    # Validate team access if team-shared
    if agent_data.team_id and agent_data.visibility == "team":
        is_member = await _is_team_member(db, user_id, agent_data.team_id)
        if not is_member:
            raise ValueError("User is not a member of the specified team")
    
    # Create agent
    agent = CustomAgent(
        user_id=user_id,
        team_id=agent_data.team_id if agent_data.visibility == "team" else None,
        name=agent_data.name,
        description=agent_data.description,
        icon=agent_data.icon,
        visibility=agent_data.visibility,
        category=agent_data.category,
        template_id=agent_data.template_id,
        model_name=agent_data.model_name,
        system_prompt=agent_data.system_prompt,
        temperature=agent_data.temperature,
        max_tokens=agent_data.max_tokens,
        top_p=agent_data.top_p,
        enabled_tools=agent_data.enabled_tools,
        tool_config=agent_data.tool_config,
    )
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    return agent


async def update_agent(
    db: AsyncSession,
    agent_id: UUID,
    user_id: UUID,
    agent_data: CustomAgentUpdate
) -> CustomAgent:
    """
    Update an existing agent.
    
    Args:
        db: Database session
        agent_id: ID of agent to update
        user_id: ID of user making the update
        agent_data: Updated agent configuration
    
    Returns:
        Updated CustomAgent
    
    Raises:
        ValueError: If agent not found or user lacks permission
    """
    # Get agent
    result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise ValueError("Agent not found")
    
    # Check permission (only owner can edit)
    if agent.user_id != user_id:
        raise ValueError("Only the agent owner can edit it")
    
    # Update fields
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    await db.commit()
    await db.refresh(agent)
    
    return agent


async def delete_agent(
    db: AsyncSession,
    agent_id: UUID,
    user_id: UUID
) -> None:
    """
    Delete an agent (soft delete by setting visibility).
    
    Args:
        db: Database session
        agent_id: ID of agent to delete
        user_id: ID of user deleting the agent
    
    Raises:
        ValueError: If agent not found or user lacks permission
    """
    result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise ValueError("Agent not found")
    
    if agent.user_id != user_id:
        raise ValueError("Only the agent owner can delete it")
    
    await db.delete(agent)
    await db.commit()


async def get_agent_by_id(
    db: AsyncSession,
    agent_id: UUID,
    user_id: UUID
) -> Optional[CustomAgent]:
    """
    Get an agent by ID.
    
    Checks visibility permissions:
    - Private: Only owner can see
    - Team: Owner + team members can see
    - Public: Anyone can see
    
    Args:
        db: Database session
        agent_id: ID of agent
        user_id: ID of requesting user
    
    Returns:
        CustomAgent if found and accessible, None otherwise
    """
    result = await db.execute(
        select(CustomAgent)
        .options(selectinload(CustomAgent.knowledge_files))
        .where(CustomAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        return None
    
    # Check visibility
    if agent.visibility == "private" and agent.user_id != user_id:
        return None
    
    if agent.visibility == "team":
        # Check if user is owner or team member
        if agent.user_id != user_id:
            if not agent.team_id:
                return None
            is_member = await _is_team_member(db, user_id, agent.team_id)
            if not is_member:
                return None
    
    # Public agents are visible to all
    return agent


async def get_user_agents(
    db: AsyncSession,
    user_id: UUID,
    include_team: bool = True,
    include_public: bool = False
) -> List[CustomAgent]:
    """
    Get all agents accessible to a user.
    
    Args:
        db: Database session
        user_id: ID of user
        include_team: Include agents shared with user's teams
        include_public: Include public marketplace agents
    
    Returns:
        List of CustomAgent objects with run_count populated
    """
    from app.models.analytics import AgentAnalytics
    from sqlalchemy import func
    
    conditions = [CustomAgent.user_id == user_id]  # User's own agents
    
    if include_team:
        # Get user's team IDs
        team_result = await db.execute(
            select(TeamMember.team_id).where(TeamMember.user_id == user_id)
        )
        team_ids = [row[0] for row in team_result.all()]
        
        if team_ids:
            conditions.append(
                and_(
                    CustomAgent.visibility == "team",
                    CustomAgent.team_id.in_(team_ids)
                )
            )
    
    if include_public:
        conditions.append(CustomAgent.visibility == "public")
    
    # Query agents with analytics data joined
    result = await db.execute(
        select(
            CustomAgent,
            func.coalesce(func.sum(AgentAnalytics.total_runs), 0).label("run_count")
        )
        .outerjoin(AgentAnalytics, CustomAgent.id == AgentAnalytics.agent_id)
        .where(or_(*conditions))
        .group_by(CustomAgent.id)
        .order_by(CustomAgent.created_at.desc())
    )
    
    # Add run_count as attribute to each agent
    agents = []
    for agent, run_count in result.all():
        agent.run_count = run_count
        agents.append(agent)
    
    return agents


async def get_marketplace_agents(
    db: AsyncSession,
    category: Optional[str] = None,
    limit: int = 50
) -> List[CustomAgent]:
    """
    Get public marketplace agents.
    
    Args:
        db: Database session
        category: Optional category filter
        limit: Maximum number of agents to return
    
    Returns:
        List of public CustomAgent objects with run_count populated
    """
    from app.models.analytics import AgentAnalytics
    from sqlalchemy import func
    
    query = (
        select(
            CustomAgent,
            func.coalesce(func.sum(AgentAnalytics.total_runs), 0).label("run_count")
        )
        .outerjoin(AgentAnalytics, CustomAgent.id == AgentAnalytics.agent_id)
        .where(CustomAgent.visibility == "public")
        .group_by(CustomAgent.id)
    )
    
    if category:
        query = query.where(CustomAgent.category == category)
    
    query = query.order_by(CustomAgent.star_count.desc()).limit(limit)
    
    result = await db.execute(query)
    
    # Add run_count as attribute to each agent
    agents = []
    for agent, run_count in result.all():
        agent.run_count = run_count
        agents.append(agent)
    
    return agents


async def clone_agent(
    db: AsyncSession,
    agent_id: UUID,
    user_id: UUID,
    custom_name: Optional[str] = None
) -> CustomAgent:
    """
    Clone an agent (install from marketplace or duplicate own agent).
    
    Args:
        db: Database session
        agent_id: ID of agent to clone
        user_id: ID of user cloning the agent
        custom_name: Optional custom name for the clone
    
    Returns:
        New CustomAgent (clone)
    """
    # Get source agent
    source = await get_agent_by_id(db, agent_id, user_id)
    if not source:
        raise ValueError("Agent not found or not accessible")
    
    # Increment install count if cloning a public agent
    if source.visibility == "public" and source.user_id != user_id:
        source.install_count += 1
    
    # Create clone
    clone = CustomAgent(
        user_id=user_id,
        team_id=None,  # Clone is always private initially
        name=custom_name or f"{source.name} (Copy)",
        description=source.description,
        icon=source.icon,
        visibility="private",
        category=source.category,
        template_id=source.id if source.visibility == "public" else source.template_id,
        model_name=source.model_name,
        system_prompt=source.system_prompt,
        temperature=source.temperature,
        max_tokens=source.max_tokens,
        top_p=source.top_p,
        enabled_tools=source.enabled_tools,
        tool_config=source.tool_config,
    )
    
    db.add(clone)
    await db.commit()
    await db.refresh(clone)
    
    return clone


async def validate_agent_config(agent_data: CustomAgentCreate) -> None:
    """
    Validate agent configuration.
    
    Args:
        agent_data: Agent configuration to validate
    
    Raises:
        ValueError: If configuration is invalid
    """
    # Validate model name (basic check)
    valid_model_prefixes = ["claude-", "gpt-", "gemini-"]
    if not any(agent_data.model_name.startswith(prefix) for prefix in valid_model_prefixes):
        raise ValueError(f"Invalid model name: {agent_data.model_name}")
    
    # Validate system prompt length
    if len(agent_data.system_prompt) < 10:
        raise ValueError("System prompt is too short (minimum 10 characters)")
    
    if len(agent_data.system_prompt) > 50000:
        raise ValueError("System prompt is too long (maximum 50,000 characters)")
    
    # Validate tools
    valid_tools = ["board", "web_search", "code_execution", "code_analysis", "knowledge_base", "git", "weather", "mcp", "notebook"]
    invalid_tools = [tool for tool in agent_data.enabled_tools if tool not in valid_tools]
    if invalid_tools:
        raise ValueError(f"Invalid tools: {', '.join(invalid_tools)}")


# Helper functions

async def _is_team_member(db: AsyncSession, user_id: UUID, team_id: UUID) -> bool:
    """Check if user is a member of a team."""
    result = await db.execute(
        select(TeamMember).where(
            and_(
                TeamMember.user_id == user_id,
                TeamMember.team_id == team_id
            )
        )
    )
    return result.scalar_one_or_none() is not None
