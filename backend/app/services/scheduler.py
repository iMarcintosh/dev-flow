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
    if not base_time:
        base_time = datetime.utcnow()
    
    try:
        cron = croniter(cron_expression, base_time)
        return cron.get_next(datetime)
    except Exception as e:
        raise ValueError(f"Invalid cron expression {cron_expression}: {e}")


def register_scheduled_agent(agent_id: str, agent_name: str, cron_expression: str):
    """
    Register an agent with Celery Beat for scheduled execution.
    
    Args:
        agent_id: UUID string of the agent
        agent_name: Human-readable name
        cron_expression: Cron format schedule
    """
    try:
        cron_kwargs = parse_cron_schedule(cron_expression)
        schedule = crontab(**cron_kwargs)
        
        # Register with Celery Beat
        celery_app.conf.beat_schedule[f"custom-agent-{agent_id}"] = {
            "task": "run_custom_agent_scheduled",
            "schedule": schedule,
            "args": (agent_id,),
        }
        
        print(f"✓ Registered scheduled agent: {agent_name} ({agent_id}) - {cron_expression}")
        
    except Exception as e:
        print(f"✗ Failed to register agent {agent_name}: {e}")


def unregister_scheduled_agent(agent_id: str):
    """
    Remove an agent from Celery Beat schedule.
    
    Args:
        agent_id: UUID string of the agent
    """
    task_name = f"custom-agent-{agent_id}"
    if task_name in celery_app.conf.beat_schedule:
        del celery_app.conf.beat_schedule[task_name]
        print(f"✓ Unregistered scheduled agent: {agent_id}")


async def load_scheduled_agents(db: AsyncSession):
    """
    Load all scheduled custom agents and register them with Celery Beat.
    
    This is called during worker/beat startup.
    
    Args:
        db: Database session
    """
    try:
        # Query all scheduled agents
        stmt = select(CustomAgent).where(
            CustomAgent.trigger == "scheduled",
            CustomAgent.schedule_enabled == True,
            CustomAgent.schedule.isnot(None)
        )
        
        result = await db.execute(stmt)
        agents = result.scalars().all()
        
        # Register each agent
        for agent in agents:
            # Calculate next run if not set
            if not agent.next_scheduled_run and agent.schedule:
                agent.next_scheduled_run = calculate_next_run(agent.schedule)
            
            # Register with Celery Beat
            register_scheduled_agent(str(agent.id), agent.name, agent.schedule)
        
        await db.commit()
        
        print(f"✓ Loaded {len(agents)} scheduled custom agents")
        return len(agents)
        
    except Exception as e:
        print(f"✗ Failed to load scheduled agents: {e}")
        await db.rollback()
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

@shared_task(name="run_custom_agent_scheduled", bind=True)
def run_custom_agent_scheduled(self, agent_id: str):
    """
    Celery task to run a custom agent on schedule.
    
    Args:
        agent_id: UUID of the custom agent
    """
    print(f"▶ Scheduled task triggered for agent: {agent_id}")
    
    # Import here to avoid issues
    from app.database import SessionLocal
    from sqlalchemy import select as sync_select, update
    from app.models.custom_agent import CustomAgent as SyncCustomAgent
    
    # Use synchronous session
    db = SessionLocal()
    try:
        # Get agent (synchronous)
        agent = db.query(SyncCustomAgent).filter(SyncCustomAgent.id == UUID(agent_id)).first()
        
        if not agent:
            print(f"✗ Agent {agent_id} not found")
            return
        
        if not agent.schedule_enabled:
            print(f"✗ Agent {agent.name} schedule is disabled")
            return
        
        print(f"▶ Running scheduled agent: {agent.name}")
        
        # Update timestamps
        agent.last_scheduled_run = datetime.utcnow()
        if agent.schedule:
            agent.next_scheduled_run = calculate_next_run(agent.schedule)
        
        db.commit()
        
        # Execute the agent using sync runner
        try:
            from app.agent.sync_agent_runner import run_custom_agent_sync
            
            # Use system prompt as input for scheduled runs
            input_text = agent.system_prompt
            
            result = run_custom_agent_sync(
                agent_id=UUID(agent_id),
                user_id=agent.user_id,
                input_text=input_text,
            )
            
            if result and result.get('success'):
                response = result.get('response', '')
                print(f"✓ Completed scheduled run for {agent.name}")
                print(f"  Response: {response[:200]}..." if len(response) > 200 else f"  Response: {response}")
                print(f"  Next run: {agent.next_scheduled_run}")
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                print(f"✗ Agent execution failed: {error}")
                print(f"  Next run: {agent.next_scheduled_run}")
                
        except Exception as e:
            print(f"✗ Error in agent execution: {e}")
            import traceback
            traceback.print_exc()
            print(f"  Next run: {agent.next_scheduled_run}")
        
    except Exception as e:
        print(f"✗ Error in scheduled task: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
