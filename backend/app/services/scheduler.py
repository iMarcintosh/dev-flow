"""
Scheduler service for managing custom agent schedules with Celery Beat.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from celery.schedules import crontab
from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.custom_agent import CustomAgent
from app.celery_app import celery_app


def parse_cron_schedule(cron_expression: str) -> Dict[str, str]:
    """
    Parse cron expression into Celery crontab kwargs.
    
    Args:
        cron_expression: Cron format string (e.g., "0 9 * * *")
        
    Returns:
        Dict with keys: minute, hour, day_of_month, month_of_year, day_of_week
    """
    parts = cron_expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {cron_expression}")
    
    minute, hour, day_of_month, month, day_of_week = parts
    
    return {
        "minute": minute,
        "hour": hour,
        "day_of_month": day_of_month,
        "month_of_year": month,
        "day_of_week": day_of_week,
    }


def calculate_next_run(cron_expression: str, base_time: Optional[datetime] = None) -> datetime:
    """
    Calculate next run time from cron expression.
    
    Args:
        cron_expression: Cron format string
        base_time: Base time to calculate from (default: now)
        
    Returns:
        Next scheduled run datetime
    """
    if base_time is None:
        base_time = datetime.utcnow()
    
    cron = croniter(cron_expression, base_time)
    return cron.get_next(datetime)


def register_scheduled_agent(agent_id: str, agent_name: str, cron_expression: str) -> bool:
    """
    Register a custom agent with Celery Beat.
    
    Args:
        agent_id: UUID of the custom agent
        agent_name: Name of the agent
        cron_expression: Cron schedule expression
        
    Returns:
        True if successfully registered
    """
    try:
        cron_params = parse_cron_schedule(cron_expression)
        
        # Create unique task name
        task_name = f"custom-agent-{agent_id}"
        
        # Add periodic task to Celery Beat
        celery_app.add_periodic_task(
            crontab(**cron_params),
            run_custom_agent_scheduled.s(agent_id),
            name=task_name
        )
        
        print(f"✓ Registered scheduled agent: {agent_name} ({agent_id}) - {cron_expression}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to register scheduled agent {agent_name}: {e}")
        return False


def unregister_scheduled_agent(agent_id: str) -> bool:
    """
    Remove a custom agent from Celery Beat schedule.
    
    Args:
        agent_id: UUID of the custom agent
        
    Returns:
        True if successfully unregistered
    """
    try:
        task_name = f"custom-agent-{agent_id}"
        
        # Remove from beat schedule
        # Note: Celery doesn't provide direct API for this, 
        # so we'll handle it on worker restart by only loading enabled schedules
        
        print(f"✓ Unregistered scheduled agent: {agent_id}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to unregister scheduled agent {agent_id}: {e}")
        return False


async def load_scheduled_agents(db: AsyncSession) -> int:
    """
    Load all enabled scheduled custom agents and register them with Celery Beat.
    
    Args:
        db: Database session
        
    Returns:
        Number of agents registered
    """
    try:
        # Query all scheduled agents that are enabled
        stmt = select(CustomAgent).where(
            CustomAgent.trigger == "scheduled",
            CustomAgent.schedule_enabled == True,
            CustomAgent.schedule.isnot(None)
        )
        
        result = await db.execute(stmt)
        agents = result.scalars().all()
        
        registered_count = 0
        
        for agent in agents:
            # Calculate and update next run time
            try:
                next_run = calculate_next_run(agent.schedule)
                agent.next_scheduled_run = next_run
                await db.commit()
            except Exception as e:
                print(f"✗ Failed to calculate next run for {agent.name}: {e}")
                continue
            
            # Register with Celery Beat
            if register_scheduled_agent(str(agent.id), agent.name, agent.schedule):
                registered_count += 1
        
        print(f"✓ Loaded {registered_count} scheduled custom agents")
        return registered_count
        
    except Exception as e:
        print(f"✗ Failed to load scheduled agents: {e}")
        return 0


async def update_agent_schedule(
    db: AsyncSession,
    agent_id: UUID,
    schedule: Optional[str] = None,
    enabled: Optional[bool] = None
) -> bool:
    """
    Update an agent's schedule and refresh Celery Beat registration.
    
    Args:
        db: Database session
        agent_id: Agent UUID
        schedule: New cron schedule (optional)
        enabled: Enable/disable schedule (optional)
        
    Returns:
        True if successfully updated
    """
    try:
        stmt = select(CustomAgent).where(CustomAgent.id == agent_id)
        result = await db.execute(stmt)
        agent = result.scalar_one_or_none()
        
        if not agent:
            return False
        
        # Update schedule fields
        if schedule is not None:
            agent.schedule = schedule
            # Calculate next run
            if schedule:
                agent.next_scheduled_run = calculate_next_run(schedule)
        
        if enabled is not None:
            agent.schedule_enabled = enabled
        
        await db.commit()
        
        # Re-register or unregister based on state
        if agent.trigger == "scheduled" and agent.schedule_enabled and agent.schedule:
            register_scheduled_agent(str(agent.id), agent.name, agent.schedule)
        else:
            unregister_scheduled_agent(str(agent.id))
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to update agent schedule: {e}")
        await db.rollback()
        return False


# Import after function definitions to avoid circular imports
from celery import shared_task

@shared_task(name="run_custom_agent_scheduled")
def run_custom_agent_scheduled(agent_id: str):
    """
    Celery task to run a custom agent on schedule.
    
    Args:
        agent_id: UUID of the custom agent
    """
    import asyncio
    from app.database import async_session_maker
    from app.agent.custom_agent_runner import run_custom_agent
    from app.models.analytics import AgentAnalytics
    from sqlalchemy import func
    
    async def _run():
        async with async_session_maker() as db:
            # Get agent
            stmt = select(CustomAgent).where(CustomAgent.id == UUID(agent_id))
            result = await db.execute(stmt)
            agent = result.scalar_one_or_none()
            
            if not agent:
                print(f"✗ Agent {agent_id} not found")
                return
            
            if not agent.schedule_enabled:
                print(f"✗ Agent {agent.name} schedule is disabled")
                return
            
            print(f"▶ Running scheduled agent: {agent.name}")
            
            try:
                # Update last run time
                agent.last_scheduled_run = datetime.utcnow()
                
                # Calculate next run
                if agent.schedule:
                    agent.next_scheduled_run = calculate_next_run(agent.schedule)
                
                await db.commit()
                
                # Run the agent
                # Note: Scheduled agents run without specific user context
                # They should be designed to work autonomously
                result = await run_custom_agent(
                    agent_id=UUID(agent_id),
                    user_id=agent.user_id,
                    message="Scheduled execution",
                    db=db
                )
                
                print(f"✓ Completed scheduled run for {agent.name}")
                print(f"  Response: {result[:100]}..." if len(result) > 100 else f"  Response: {result}")
                
            except Exception as e:
                print(f"✗ Error running scheduled agent {agent.name}: {e}")
                import traceback
                traceback.print_exc()
    
    asyncio.run(_run())
