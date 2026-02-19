"""Chat API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import uuid

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage
from app.agent.registry import registry
from app.agent.base_agent import AgentInput
from app.models.agent_run import AgentRun, AgentRunStatus

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat message request."""
    project_id: str
    message: str


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: uuid.UUID
    role: str
    content: str
    created_at: str
    
    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Chat API response."""
    message: str
    referenced_items: List[dict] = []


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a chat message and get AI response.
    
    The chat agent has context about the board and can:
    - Answer questions about items
    - Provide project statistics
    - Reference specific items
    """
    # Get chat agent
    agent = registry.get("chat_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Chat agent not available")
    
    # Create agent run
    run = AgentRun(
        agent_name=agent.name,
        trigger="chat",
        status=AgentRunStatus.PENDING,
        input={
            "project_id": request.project_id,
            "user_id": str(current_user.id),
            "message": request.message
        },
        created_by=current_user.id
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    
    # Prepare input
    agent_input = AgentInput(
        project_id=request.project_id,
        user_id=str(current_user.id),
        data={"message": request.message}
    )
    
    # Run agent synchronously (for chat, we want immediate response)
    result = await agent.run(agent_input, str(run.id))
    
    # Update run with result
    run.status = AgentRunStatus.DONE if result.success else AgentRunStatus.FAILED
    run.output = result.output
    if not result.success:
        run.error_message = result.message
    await db.commit()
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.message)
    
    return ChatResponse(
        message=result.output.get("message", ""),
        referenced_items=result.output.get("referenced_items", [])
    )


@router.get("/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    project_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for a project."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    # Reverse to show oldest first
    messages = list(reversed(messages))
    
    return [
        ChatMessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at.isoformat()
        )
        for msg in messages
    ]
