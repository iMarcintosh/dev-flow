"""
API endpoints for Custom Agent management.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel

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
    from app.api.routes.models import get_redis

    agents = await custom_agent_service.get_user_agents(
        db=db,
        user_id=current_user.id,
        include_team=include_team,
        include_public=include_public,
    )

    redis_client = await get_redis()
    result = []
    for agent in agents:
        resp = CustomAgentResponse.model_validate(agent)
        if agent.trigger == 'scheduled':
            key = f"devflow:beat:custom-agent-{agent.id}"
            resp.beat_registered = bool(await redis_client.exists(key))
        else:
            resp.beat_registered = True
        result.append(resp)
    return result


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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new custom agent.
    
    Can be created from scratch or from a template.
    Supports scheduling for automated execution.
    """
    try:
        # Validate scheduling
        if agent_data.trigger == 'scheduled' and not agent_data.schedule:
            raise ValueError('Schedule is required when trigger is set to "scheduled"')
        
        # Validate configuration
        await custom_agent_service.validate_agent_config(agent_data)
        
        # Create agent
        agent = await custom_agent_service.create_agent(
            db=db,
            user_id=current_user.id,
            agent_data=agent_data,
        )
        
        # Register with scheduler if scheduled
        if agent.trigger == 'scheduled' and agent.schedule and agent.schedule_enabled:
            from app.services.scheduler import register_scheduled_agent, calculate_next_run
            
            # Calculate next run
            agent.next_scheduled_run = calculate_next_run(agent.schedule)
            await db.commit()
            await db.refresh(agent)
            
            # Register with Celery Beat
            background_tasks.add_task(
                register_scheduled_agent,
                str(agent.id),
                agent.name,
                agent.schedule
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
    from app.api.routes.models import get_redis

    agent = await custom_agent_service.get_agent_by_id(
        db=db,
        agent_id=agent_id,
        user_id=current_user.id,
    )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    redis_client = await get_redis()
    resp = CustomAgentResponse.model_validate(agent)
    if agent.trigger == 'scheduled':
        key = f"devflow:beat:custom-agent-{agent.id}"
        resp.beat_registered = bool(await redis_client.exists(key))
    else:
        resp.beat_registered = True
    return resp


@router.put("/{agent_id}", response_model=CustomAgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: CustomAgentUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing agent.
    
    Only the agent owner can update it.
    Updates to schedule will re-register the agent with Celery Beat.
    """
    try:
        agent = await custom_agent_service.update_agent(
            db=db,
            agent_id=agent_id,
            user_id=current_user.id,
            agent_data=agent_data,
        )
        
        # Update schedule if changed (including trigger changes)
        if (agent_data.schedule is not None or 
            agent_data.schedule_enabled is not None or 
            agent_data.trigger is not None):
            from app.services.scheduler import update_agent_schedule
            
            background_tasks.add_task(
                update_agent_schedule,
                db,
                agent_id,
                agent_data.schedule,
                agent_data.schedule_enabled
            )
        
        return agent
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an agent.
    
    Only the agent owner can delete it.
    This will also delete all associated conversations and knowledge files.
    Removes agent from schedule if it was scheduled.
    """
    try:
        # Get agent to check if scheduled
        agent = await custom_agent_service.get_agent_by_id(
            db=db,
            agent_id=agent_id,
            user_id=current_user.id,
        )
        
        # Unregister from scheduler if needed
        if agent and agent.trigger == 'scheduled':
            from app.services.scheduler import unregister_scheduled_agent
            background_tasks.add_task(unregister_scheduled_agent, str(agent_id))
        
        # Delete agent
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


@router.get("/scheduled", response_model=List[CustomAgentResponse])
async def list_scheduled_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all scheduled agents for the current user.
    
    Returns agents with trigger='scheduled' and schedule_enabled=true.
    """
    from sqlalchemy import select
    
    stmt = select(CustomAgent).where(
        CustomAgent.user_id == current_user.id,
        CustomAgent.trigger == "scheduled",
        CustomAgent.schedule_enabled == True,
    )
    
    result = await db.execute(stmt)
    agents = result.scalars().all()
    
    return agents


@router.post("/{agent_id}/trigger", status_code=202)
async def trigger_agent_manually(
    agent_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger a scheduled agent to run immediately.
    
    Useful for testing scheduled agents without waiting for the schedule.
    Returns immediately and runs the agent in the background.
    """
    # Verify agent exists and user has access
    agent = await custom_agent_service.get_agent_by_id(
        db=db,
        agent_id=agent_id,
        user_id=current_user.id,
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the agent owner can trigger it")
    
    # Trigger in background
    from app.services.scheduler import run_custom_agent_scheduled
    background_tasks.add_task(run_custom_agent_scheduled.delay, str(agent_id))
    
    return {
        "status": "triggered",
        "agent_id": str(agent_id),
        "agent_name": agent.name,
        "message": "Agent execution started in background"
    }


@router.patch("/{agent_id}/schedule", response_model=CustomAgentResponse)
async def update_schedule(
    agent_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    schedule: Optional[str] = Query(None, description="Cron expression"),
    enabled: Optional[bool] = Query(None, description="Enable/disable schedule"),
):
    """
    Update agent schedule settings.
    
    Args:
        schedule: New cron expression (e.g., "0 9 * * *")
        enabled: Enable or disable the schedule
    
    At least one parameter must be provided.
    """
    if schedule is None and enabled is None:
        raise HTTPException(status_code=400, detail="Must provide schedule or enabled parameter")
    
    # Verify agent exists and user has access
    agent = await custom_agent_service.get_agent_by_id(
        db=db,
        agent_id=agent_id,
        user_id=current_user.id,
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if agent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the agent owner can update schedule")
    
    # Validate cron if provided
    if schedule is not None:
        from app.schemas.custom_agent import validate_cron_expression
        if not validate_cron_expression(schedule):
            raise HTTPException(status_code=400, detail="Invalid cron expression")
    
    # Update schedule
    from app.services.scheduler import update_agent_schedule
    
    success = await update_agent_schedule(
        db=db,
        agent_id=agent_id,
        schedule=schedule,
        enabled=enabled
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update schedule")
    
    # Refresh agent to get updated values
    await db.refresh(agent)
    
    return agent


# Scheduled Run Result Schema
class ScheduledRunResult(BaseModel):
    id: UUID
    agent_id: UUID
    status: str
    input_text: Optional[str]
    response: Optional[str]
    error: Optional[str]
    response_time: Optional[float]
    tools_used: Optional[int]
    executed_at: datetime


@router.get("/{agent_id}/scheduled-runs", response_model=List[ScheduledRunResult])
async def get_scheduled_runs(
    agent_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get scheduled run history for an agent.
    
    Returns recent scheduled executions with results.
    """
    # Verify agent access
    result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Check access (owner or team member for team agents)
    if agent.visibility == "private" and agent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Fetch runs
    query = text("""
        SELECT id, agent_id, status, input_text, response, error, 
               response_time, tools_used, executed_at
        FROM scheduled_agent_runs
        WHERE agent_id = :agent_id
        ORDER BY executed_at DESC
        LIMIT :limit
    """)
    
    result = await db.execute(query, {"agent_id": str(agent_id), "limit": limit})
    rows = result.fetchall()
    
    runs = []
    for row in rows:
        runs.append(ScheduledRunResult(
            id=row[0],
            agent_id=row[1],
            status=row[2],
            input_text=row[3],
            response=row[4],
            error=row[5],
            response_time=row[6],
            tools_used=row[7],
            executed_at=row[8],
        ))
    
    return runs


class ConversationResult(BaseModel):
    id: UUID
    agent_id: UUID
    user_id: UUID
    project_id: Optional[UUID]
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime


@router.get("/{agent_id}/conversations", response_model=List[ConversationResult])
async def get_agent_conversations(
    agent_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CustomAgent).where(CustomAgent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if agent.visibility == "private" and agent.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    query = text("""
        SELECT id, agent_id, user_id, project_id, title, message_count,
               created_at, updated_at
        FROM agent_conversations
        WHERE agent_id = :agent_id AND user_id = :user_id
        ORDER BY updated_at DESC
        LIMIT :limit
    """)
    result = await db.execute(query, {
        "agent_id": str(agent_id), "user_id": str(current_user.id), "limit": limit
    })
    return [ConversationResult(
        id=r[0], agent_id=r[1], user_id=r[2], project_id=r[3],
        title=r[4], message_count=r[5], created_at=r[6], updated_at=r[7]
    ) for r in result.fetchall()]
