from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.agent_run import AgentRun, AgentRunStatus, AgentTrigger
from app.api.routes.auth import get_current_user
from app.agent.registry import registry
from app.agent.base_agent import AgentInput
from app.services.websocket import manager
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()


class StartAgentRequest(BaseModel):
    project_id: str
    data: dict


class AgentRunResponse(BaseModel):
    id: uuid.UUID
    agent_name: str
    status: str
    input: Optional[dict]
    output: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            uuid.UUID: str
        }


@router.get("/", response_model=List[dict])
async def list_agents(current_user: User = Depends(get_current_user)):
    """List all registered agents."""
    return registry.list_agents()


@router.post("/{agent_name}/run", response_model=dict)
async def start_agent(
    agent_name: str,
    request: StartAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start an agent run directly (not via Celery)."""
    agent = registry.get(agent_name)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )
    
    # Create agent run record
    agent_run = AgentRun(
        agent_name=agent_name,
        trigger=AgentTrigger.MANUAL,
        status=AgentRunStatus.RUNNING,
        input={"project_id": request.project_id, "data": request.data},
        created_by=current_user.id,
        started_at=datetime.utcnow()
    )
    
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)
    
    # Execute agent directly in FastAPI (not Celery)
    try:
        agent_input = AgentInput(
            project_id=request.project_id,
            user_id=str(current_user.id),
            data=request.data
        )
        
        # Run agent
        result = await agent.run(agent_input, str(agent_run.id))
        
        # Update status
        agent_run.status = AgentRunStatus.DONE if result.success else AgentRunStatus.FAILED
        agent_run.output = result.output
        agent_run.error_message = result.error
        agent_run.finished_at = datetime.utcnow()
        await db.commit()
        
        return {
            "run_id": str(agent_run.id),
            "status": agent_run.status.value,
            "success": result.success,
            "output": result.output,
            "message": f"Agent '{agent_name}' completed"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        agent_run.status = AgentRunStatus.FAILED
        agent_run.error_message = str(e)
        agent_run.finished_at = datetime.utcnow()
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details of an agent run."""
    result = await db.execute(
        select(AgentRun).where(AgentRun.id == run_id)
    )
    agent_run = result.scalar_one_or_none()
    
    if not agent_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found"
        )
    
    return AgentRunResponse.model_validate(agent_run)


@router.post("/runs/{run_id}/apply", response_model=dict)
async def apply_agent_results(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply agent results (import items to board)."""
    result = await db.execute(
        select(AgentRun).where(AgentRun.id == run_id)
    )
    agent_run = result.scalar_one_or_none()
    
    if not agent_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run not found"
        )
    
    if agent_run.status != AgentRunStatus.DONE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent run is not complete"
        )
    
    # Get preview from output
    preview = agent_run.output.get("preview", [])
    project_id = agent_run.input.get("project_id")
    
    if not preview or not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No items to import"
        )
    
    # Import items
    from app.models.item import Item, ItemStatus
    
    created_items = []
    for item_data in preview:
        new_item = Item(
            project_id=uuid.UUID(project_id),
            title=item_data["title"],
            description=item_data.get("description"),
            acceptance_criteria=item_data.get("acceptance_criteria"),
            type=item_data.get("type", "task"),
            priority=item_data.get("priority", "medium"),
            status=ItemStatus.BACKLOG,
            tags=item_data.get("tags", []),
            position=len(created_items) + 1.0,
            created_by=current_user.id
        )
        db.add(new_item)
        created_items.append(new_item)
    
    await db.commit()
    
    return {
        "success": True,
        "items_created": len(created_items),
        "item_ids": [str(item.id) for item in created_items]
    }


@router.websocket("/ws/{run_id}")
async def agent_websocket(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for live agent updates."""
    await manager.connect(websocket, run_id)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back (optional)
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)


@router.get("/{agent_name}/runs", response_model=List[AgentRunResponse])
async def get_agent_runs(
    agent_name: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get run history for a specific agent."""
    stmt = (
        select(AgentRun)
        .where(AgentRun.agent_name == agent_name)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    runs = result.scalars().all()
    
    return [AgentRunResponse.model_validate(run) for run in runs]


@router.get("/runs/{run_id}/logs")
async def get_run_logs(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get logs for a specific agent run."""
    from app.models.agent_run import AgentRunLog
    
    stmt = (
        select(AgentRunLog)
        .where(AgentRunLog.agent_run_id == run_id)
        .order_by(AgentRunLog.timestamp.asc())
    )
    
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "level": log.level,
            "message": log.message,
            "timestamp": log.timestamp.isoformat()
        }
        for log in logs
    ]


@router.get("/{agent_name}/status")
async def get_agent_status(
    agent_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current status of an agent."""
    agent = registry.get(agent_name)
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Get latest run
    stmt = (
        select(AgentRun)
        .where(AgentRun.agent_name == agent_name)
        .order_by(AgentRun.created_at.desc())
        .limit(1)
    )
    
    result = await db.execute(stmt)
    latest_run = result.scalar_one_or_none()
    
    # Get total runs
    from sqlalchemy import func
    count_stmt = select(func.count(AgentRun.id)).where(AgentRun.agent_name == agent_name)
    total_result = await db.execute(count_stmt)
    total_runs = total_result.scalar()
    
    # Get success rate
    success_stmt = (
        select(func.count(AgentRun.id))
        .where(AgentRun.agent_name == agent_name)
        .where(AgentRun.status == AgentRunStatus.DONE)
    )
    success_result = await db.execute(success_stmt)
    successful_runs = success_result.scalar()
    
    return {
        "agent": agent.to_dict(),
        "status": latest_run.status.value if latest_run else "idle",
        "last_run": {
            "id": str(latest_run.id),
            "started_at": latest_run.started_at.isoformat() if latest_run.started_at else None,
            "finished_at": latest_run.finished_at.isoformat() if latest_run.finished_at else None,
            "status": latest_run.status.value
        } if latest_run else None,
        "stats": {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0
        }
    }
