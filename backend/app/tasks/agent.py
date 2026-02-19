"""Celery tasks for agent execution (scheduled agents only)."""

from app.celery_app import celery_app
from app.agent.registry import registry
from app.agent.base_agent import AgentInput
from app.database import SessionLocal  # Sync session for Celery
from app.models.agent_run import AgentRun, AgentRunStatus
import uuid
import asyncio
from datetime import datetime


@celery_app.task
def run_agent_task(agent_name: str, run_id: str, input_data: dict):
    """
    Execute an agent in Celery worker (for scheduled agents only).
    Uses synchronous database session to avoid asyncio event loop issues.
    """
    agent = registry.get(agent_name)
    
    if not agent:
        print(f"✗ Agent '{agent_name}' not found")
        return
    
    db = SessionLocal()
    
    try:
        # Update status to RUNNING
        agent_run = db.query(AgentRun).filter(AgentRun.id == uuid.UUID(run_id)).first()
        
        if agent_run:
            agent_run.status = AgentRunStatus.RUNNING
            agent_run.started_at = datetime.utcnow()
            db.commit()
            print(f"▶ Running scheduled agent '{agent_name}' (run_id: {run_id})")
        
        # Create input
        agent_input = AgentInput(
            project_id=input_data["project_id"],
            user_id=input_data["user_id"],
            data=input_data["data"]
        )
        
        # Run agent (asyncio.run creates new event loop for async agent code)
        result = asyncio.run(agent.run(agent_input, run_id))
        
        # Update status with result
        agent_run = db.query(AgentRun).filter(AgentRun.id == uuid.UUID(run_id)).first()
        
        if agent_run:
            agent_run.status = AgentRunStatus.DONE if result.success else AgentRunStatus.FAILED
            agent_run.output = result.output
            agent_run.error_message = result.error
            agent_run.finished_at = datetime.utcnow()
            db.commit()
        
        if result.success:
            print(f"✓ Scheduled agent '{agent_name}' completed successfully")
        else:
            print(f"✗ Scheduled agent '{agent_name}' failed: {result.error}")
        
    except Exception as e:
        print(f"✗ Error running scheduled agent '{agent_name}': {e}")
        import traceback
        traceback.print_exc()
        
        # Update status to failed
        agent_run = db.query(AgentRun).filter(AgentRun.id == uuid.UUID(run_id)).first()
        
        if agent_run:
            agent_run.status = AgentRunStatus.FAILED
            agent_run.error_message = str(e)
            agent_run.finished_at = datetime.utcnow()
            db.commit()
    
    finally:
        db.close()

