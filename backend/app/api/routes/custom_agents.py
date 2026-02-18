"""
API endpoints for Custom Agent management.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.models.custom_agent import CustomAgent
from app.schemas.custom_agent import (
    CustomAgentCreate,
    CustomAgentUpdate,
    CustomAgentResponse,
    AgentTemplate,
)
from app.services import custom_agent_service
from app.agent import templates


router = APIRouter(prefix="/api/custom-agents", tags=["custom-agents"])


@router.get("/templates", response_model=List[AgentTemplate])
async def list_templates():
    """
    Get all available agent templates.
    
    Returns list of pre-configured agent templates users can use as starting points.
    """
    return templates.list_templates()


@router.get("/templates/{category}", response_model=AgentTemplate)
async def get_template(category: str):
    """
    Get a specific agent template by category.
    
    Args:
        category: Template category (e.g., 'code_review', 'testing')
    """
    template = templates.get_template(category)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("", response_model=List[CustomAgentResponse])
async def list_agents(
    include_team: bool = Query(True, description="Include team-shared agents"),
    include_public: bool = Query(False, description="Include public marketplace agents"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all agents accessible to the current user.
    
    Includes:
    - User's own private agents
    - Team-shared agents (if include_team=true)
    - Public marketplace agents (if include_public=true)
    """
    agents = await custom_agent_service.get_user_agents(
        db=db,
        user_id=current_user.id,
        include_team=include_team,
        include_public=include_public,
    )
    return agents


@router.get("/marketplace", response_model=List[CustomAgentResponse])
async def list_marketplace_agents(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get public marketplace agents.
    
    Browse agents shared by other users. Can filter by category.
    """
    agents = await custom_agent_service.get_marketplace_agents(
        db=db,
        category=category,
        limit=limit,
    )
    return agents


@router.post("", response_model=CustomAgentResponse, status_code=201)
async def create_agent(
    agent_data: CustomAgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new custom agent.
    
    Can be created from scratch or from a template.
    """
    try:
        # Validate configuration
        await custom_agent_service.validate_agent_config(agent_data)
        
        # Create agent
        agent = await custom_agent_service.create_agent(
            db=db,
            user_id=current_user.id,
            agent_data=agent_data,
        )
        
        return agent
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/from-template/{category}", response_model=CustomAgentResponse, status_code=201)
async def create_from_template(
    category: str,
    custom_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create an agent from a built-in template.
    
    Args:
        category: Template category
        custom_name: Optional custom name (defaults to template name)
    """
    try:
        # Get template config
        config_dict = templates.create_agent_from_template(
            category=category,
            user_id=str(current_user.id),
            custom_name=custom_name,
        )
        
        # Convert to schema
        agent_data = CustomAgentCreate(**config_dict)
        
        # Create agent
        agent = await custom_agent_service.create_agent(
            db=db,
            user_id=current_user.id,
            agent_data=agent_data,
        )
        
        return agent
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{agent_id}", response_model=CustomAgentResponse)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific agent by ID.
    
    Respects visibility permissions:
    - Private: Only owner
    - Team: Owner + team members
    - Public: Anyone
    """
    agent = await custom_agent_service.get_agent_by_id(
        db=db,
        agent_id=agent_id,
        user_id=current_user.id,
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent


@router.put("/{agent_id}", response_model=CustomAgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: CustomAgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing agent.
    
    Only the agent owner can update it.
    """
    try:
        agent = await custom_agent_service.update_agent(
            db=db,
            agent_id=agent_id,
            user_id=current_user.id,
            agent_data=agent_data,
        )
        return agent
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an agent.
    
    Only the agent owner can delete it.
    This will also delete all associated conversations and knowledge files.
    """
    try:
        await custom_agent_service.delete_agent(
            db=db,
            agent_id=agent_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_id}/clone", response_model=CustomAgentResponse, status_code=201)
async def clone_agent(
    agent_id: UUID,
    custom_name: Optional[str] = Query(None, description="Custom name for the clone"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Clone an agent (install from marketplace or duplicate own agent).
    
    Creates a private copy of the agent for the current user.
    """
    try:
        clone = await custom_agent_service.clone_agent(
            db=db,
            agent_id=agent_id,
            user_id=current_user.id,
            custom_name=custom_name,
        )
        return clone
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_id}/star", status_code=204)
async def star_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Star/like an agent (for marketplace).
    
    TODO: Implement star tracking per user to prevent duplicate stars.
    For now, just increments the counter.
    """
    agent = await custom_agent_service.get_agent_by_id(
        db=db,
        agent_id=agent_id,
        user_id=current_user.id,
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.visibility != "public":
        raise HTTPException(status_code=400, detail="Can only star public agents")
    
    agent.star_count += 1
    await db.commit()


@router.post("/{agent_id}/test", status_code=200)
async def test_agent(
    agent_id: UUID,
    test_input: Optional[str] = Query(None, description="Test input message"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Test an agent with a sample input.
    
    Useful for validating configuration before using the agent.
    """
    from app.agent import custom_agent_runner
    
    result = await custom_agent_runner.run_custom_agent(
        db=db,
        agent_id=agent_id,
        user_id=current_user.id,
        input_text=test_input or "Hello! Please introduce yourself and describe what you can help with.",
    )
    
    return result
