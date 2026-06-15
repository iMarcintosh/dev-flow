"""
Scheduler service for managing custom agent schedules with Celery Beat (RedBeat).
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
        base_time: Base time to calculate from (default: now UTC)
        
    Returns:
        Next scheduled run datetime (timezone-aware UTC)
    """
    from datetime import timezone
    
    if not base_time:
        base_time = datetime.now(timezone.utc)
    
    try:
        cron = croniter(cron_expression, base_time)
        next_run = cron.get_next(datetime)
        
        # Ensure timezone-aware datetime
        if next_run.tzinfo is None:
            next_run = next_run.replace(tzinfo=timezone.utc)
        
        return next_run
    except Exception as e:
        raise ValueError(f"Invalid cron expression {cron_expression}: {e}")


def register_scheduled_agent(agent_id: str, agent_name: str, cron_expression: str):
    """
    Register an agent with Celery Beat via RedBeat (stored in Redis).

    Args:
        agent_id: UUID string of the agent
        agent_name: Human-readable name
        cron_expression: Cron format schedule
    """
    try:
        from redbeat import RedBeatSchedulerEntry

        cron_kwargs = parse_cron_schedule(cron_expression)
        schedule = crontab(**cron_kwargs)

        entry = RedBeatSchedulerEntry(
            f"custom-agent-{agent_id}",
            "run_custom_agent_scheduled",
            schedule,
            args=(agent_id,),
            app=celery_app,
        )
        entry.save()

        print(f"✓ Registered scheduled agent (RedBeat): {agent_name} ({agent_id}) - {cron_expression}")

    except Exception as e:
        print(f"✗ Failed to register agent {agent_name}: {e}")


def unregister_scheduled_agent(agent_id: str):
    """
    Remove an agent from Celery Beat schedule via RedBeat.

    Args:
        agent_id: UUID string of the agent
    """
    try:
        from redbeat import RedBeatSchedulerEntry

        key = f"devflow:beat:custom-agent-{agent_id}"
        entry = RedBeatSchedulerEntry.from_key(key, app=celery_app)
        entry.delete()
        print(f"✓ Unregistered scheduled agent (RedBeat): {agent_id}")
    except Exception:
        pass


async def load_scheduled_agents(db: AsyncSession) -> int:
    """
    Sync custom agents from DB → RedBeat on startup.
    Idempotent: only registers agents missing from Redis.
    """
    import redis as sync_redis
    from app.config import settings

    r = sync_redis.from_url(settings.redis_url, decode_responses=True)

    stmt = select(CustomAgent).where(
        CustomAgent.trigger == "scheduled",
        CustomAgent.schedule_enabled == True,
        CustomAgent.schedule.isnot(None),
    )
    result = await db.execute(stmt)
    agents = result.scalars().all()

    recovered = 0
    for agent in agents:
        key = f"devflow:beat:custom-agent-{agent.id}"
        if not r.exists(key):
            register_scheduled_agent(str(agent.id), agent.name, agent.schedule)
            recovered += 1

        # Always recalculate next_scheduled_run to fix stale past timestamps
        next_run = calculate_next_run(agent.schedule)
        if agent.next_scheduled_run != next_run:
            agent.next_scheduled_run = next_run

    if agents:
        await db.commit()

    print(f"✓ RedBeat recovery: {recovered}/{len(agents)} custom agents re-registered")
    return recovered


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
            
            # Use scheduled_prompt if available, otherwise fallback to generic message
            input_text = agent.scheduled_prompt or "Bitte führe deine geplante Aufgabe aus."
            
            print(f"🔄 Scheduled run for {agent.name}")
            print(f"  System Prompt: {agent.system_prompt[:80]}...")
            print(f"  User Input: {input_text[:80]}...")
            
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
