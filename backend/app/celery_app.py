import os
from celery import Celery
from app.config import settings

celery_app = Celery(
    "devflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.agent",
        "app.agent.memory.indexer",  # Real embedding tasks
        "app.services.scheduler",  # Include scheduler module
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    # RedBeat: persistent schedule stored in Redis
    beat_scheduler='redbeat.RedBeatScheduler',
    redbeat_redis_url=os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
    redbeat_key_prefix='devflow:beat:',
)

# Import agents on worker startup
@celery_app.on_after_configure.connect
def setup_agents(sender, **kwargs):
    """Import agents to trigger registration and setup scheduled tasks."""
    try:
        from app.agent.agents import task_creator, chat_agent, daily_summary
        from app.agent.registry import registry
        
        print("✓ Agents imported and registered in Celery worker")
        
        # Setup scheduled built-in agents
        scheduled_agents = registry.scheduled()
        print(f"✓ Found {len(scheduled_agents)} scheduled built-in agents")

        for agent in scheduled_agents:
            from celery.schedules import crontab

            # Parse cron schedule
            cron_parts = agent.schedule.split()
            if len(cron_parts) == 5:
                minute, hour, day_of_month, month, day_of_week = cron_parts

                # Add beat schedule dynamically
                sender.add_periodic_task(
                    crontab(
                        minute=minute,
                        hour=hour,
                        day_of_month=day_of_month,
                        month_of_year=month,
                        day_of_week=day_of_week
                    ),
                    run_scheduled_agent.s(agent.name),
                    name=f"scheduled-{agent.name}"
                )

                print(f"  ✓ Scheduled {agent.name}: {agent.schedule}")
            else:
                print(f"  ✗ Invalid cron format for {agent.name}: {agent.schedule}")

        # Recovery: sync custom agents from DB → RedBeat (idempotent)
        import asyncio
        from app.database import async_session_maker
        from app.services.scheduler import load_scheduled_agents

        async def _recover():
            async with async_session_maker() as db:
                await load_scheduled_agents(db)

        asyncio.run(_recover())

    except Exception as e:
        print(f"Error importing agents: {e}")
        import traceback
        traceback.print_exc()


# Scheduled agent task
from celery import shared_task

@shared_task(name="run_scheduled_agent")
def run_scheduled_agent(agent_name: str):
    """Run a scheduled built-in agent for all active projects."""
    import asyncio
    from app.database import async_session_maker
    from app.models.project import Project
    from app.agent.registry import registry
    from sqlalchemy import select
    
    async def _run():
        agent = registry.get(agent_name)
        if not agent:
            print(f"Agent {agent_name} not found")
            return
        
        async with async_session_maker() as db:
            # Get all projects
            stmt = select(Project)
            result = await db.execute(stmt)
            projects = result.scalars().all()
            
            print(f"Running {agent_name} for {len(projects)} projects")
            
            # Run agent for each project
            for project in projects:
                from app.tasks.agent import run_agent_task
                
                # Trigger async task for each project
                run_agent_task.delay(
                    agent_name=agent_name,
                    project_id=str(project.id),
                    user_id=str(project.owner_id),
                    data={}
                )
    
    asyncio.run(_run())
