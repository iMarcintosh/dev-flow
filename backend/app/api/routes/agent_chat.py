"""
API endpoints for Agent Chat (conversations with custom agents).
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.schemas.custom_agent import (
    AgentConversationCreate,
    AgentConversationResponse,
    AgentMessageCreate,
    AgentMessageResponse,
)
from app.services import conversation_service
from app.agent import custom_agent_runner


router = APIRouter(prefix="/api/agent-chat", tags=["agent-chat"])


@router.post("/conversations", response_model=AgentConversationResponse, status_code=201)
async def create_conversation(
    agent_id: UUID = Query(..., description="ID of the agent to chat with"),
    project_id: Optional[UUID] = Query(None, description="Optional project context"),
    title: Optional[str] = Query(None, description="Optional conversation title"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new conversation with an agent.
    
    This starts a new chat session with a custom agent.
    """
    conversation = await conversation_service.create_conversation(
        db=db,
        user_id=current_user.id,
        agent_id=agent_id,
        project_id=project_id,
        title=title,
    )
    
    return conversation


@router.get("/conversations", response_model=List[AgentConversationResponse])
async def list_conversations(
    agent_id: Optional[UUID] = Query(None, description="Filter by agent ID"),
    limit: int = Query(50, le=100, description="Maximum conversations to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all conversations for the current user.
    
    Returns conversations sorted by most recent activity.
    """
    conversations = await conversation_service.list_conversations(
        db=db,
        user_id=current_user.id,
        agent_id=agent_id,
        limit=limit,
    )
    
    return conversations


@router.get("/conversations/{conversation_id}", response_model=AgentConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific conversation by ID.
    """
    conversation = await conversation_service.get_conversation_by_id(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation and all its messages.
    """
    try:
        await conversation_service.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/conversations/{conversation_id}/title", response_model=AgentConversationResponse)
async def update_conversation_title(
    conversation_id: UUID,
    title: str = Query(..., min_length=1, max_length=255),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update conversation title.
    """
    try:
        conversation = await conversation_service.update_conversation_title(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            title=title,
        )
        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=List[AgentMessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(100, le=500, description="Maximum messages to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get message history for a conversation.
    
    Returns messages in chronological order (oldest first).
    """
    try:
        messages = await conversation_service.get_conversation_history(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            limit=limit,
        )
        return messages
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/conversations/{conversation_id}/messages", response_model=dict)
async def send_message(
    conversation_id: UUID,
    message: str = Query(..., min_length=1, description="User's message"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message in a conversation.
    
    This will:
    1. Add the user's message to the conversation
    2. Execute the agent with the message
    3. Add the agent's response to the conversation
    4. Return both messages
    """
    # Verify conversation exists and user has access
    conversation = await conversation_service.get_conversation_by_id(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Add user message
    user_message = await conversation_service.add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=message,
    )
    
    # Execute agent
    try:
        agent_result = await custom_agent_runner.run_custom_agent(
            db=db,
            agent_id=conversation.agent_id,
            user_id=current_user.id,
            input_text=message,
            project_id=conversation.project_id,
            conversation_id=conversation_id,
        )
        
        if agent_result["success"]:
            # Add agent response
            agent_message = await conversation_service.add_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=agent_result["response"],
                metadata={
                    "model": agent_result.get("model"),
                    "tools_used": agent_result.get("tools_used", []),
                },
            )
            
            return {
                "success": True,
                "user_message": {
                    "id": str(user_message.id),
                    "role": user_message.role,
                    "content": user_message.content,
                    "created_at": user_message.created_at.isoformat(),
                },
                "agent_message": {
                    "id": str(agent_message.id),
                    "role": agent_message.role,
                    "content": agent_message.content,
                    "created_at": agent_message.created_at.isoformat(),
                    "metadata": agent_message.message_metadata,
                },
            }
        else:
            # Agent execution failed
            return {
                "success": False,
                "user_message": {
                    "id": str(user_message.id),
                    "role": user_message.role,
                    "content": user_message.content,
                    "created_at": user_message.created_at.isoformat(),
                },
                "error": agent_result.get("error", "Agent execution failed"),
            }
    
    except Exception as e:
        return {
            "success": False,
            "user_message": {
                "id": str(user_message.id),
                "role": user_message.role,
                "content": user_message.content,
                "created_at": user_message.created_at.isoformat(),
            },
            "error": str(e),
        }
