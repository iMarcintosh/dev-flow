from app.celery_app import celery_app
from app.agent.registry import registry
from app.agent.base_agent import AgentInput
from app.database import async_session_maker
from app.models.agent_run import AgentRun, AgentRunStatus
from sqlalchemy import select
import uuid
import asyncio
from datetime import datetime


@celery_app.task
def run_agent_task(agent_name: str, run_id: str, input_data: dict):
    """Execute an agent asynchronously."""
    asyncio.run(_run_agent_async(agent_name, run_id, input_data))


async def _run_agent_async(agent_name: str, run_id: str, input_data: dict):
    """Async implementation of agent execution."""
    agent = registry.get(agent_name)
    
    if not agent:
        print(f"Agent '{agent_name}' not found")
        return
    
    async with async_session_maker() as db:
        # Update status to RUNNING
        result = await db.execute(select(AgentRun).where(AgentRun.id == uuid.UUID(run_id)))
        agent_run = result.scalar_one_or_none()
        
        if agent_run:
            agent_run.status = AgentRunStatus.RUNNING
            agent_run.started_at = datetime.utcnow()
            await db.commit()
    
    try:
        # Create input
        agent_input = AgentInput(
            project_id=input_data["project_id"],
            user_id=input_data["user_id"],
            data=input_data["data"]
        )
        
        # Run agent
        result = await agent.run(agent_input, run_id)
        
        # Update status
        async with async_session_maker() as db:
            db_result = await db.execute(select(AgentRun).where(AgentRun.id == uuid.UUID(run_id)))
            agent_run = db_result.scalar_one_or_none()
            
            if agent_run:
                agent_run.status = AgentRunStatus.DONE if result.success else AgentRunStatus.FAILED
                agent_run.output = result.output
                agent_run.error_message = result.error
                agent_run.finished_at = datetime.utcnow()
                await db.commit()
        
        # Broadcast completion
        from app.services.websocket import manager
        await manager.broadcast_to_run(run_id, {
            "type": "agent_finished",
            "run_id": run_id,
            "success": result.success,
            "result": result.output
        })
        
    except Exception as e:
        print(f"Error running agent: {e}")
        
        async with async_session_maker() as db:
            db_result = await db.execute(select(AgentRun).where(AgentRun.id == uuid.UUID(run_id)))
            agent_run = db_result.scalar_one_or_none()
            
            if agent_run:
                agent_run.status = AgentRunStatus.FAILED
                agent_run.error_message = str(e)
                agent_run.finished_at = datetime.utcnow()
                await db.commit()

