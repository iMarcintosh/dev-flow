"""
Conversation Service for Agent Chat.

Manages conversations and messages between users and custom agents.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.models.custom_agent import AgentConversation, AgentMessage
from app.schemas.custom_agent import (
    AgentConversationCreate,
    AgentMessageCreate,
)


async def create_conversation(
    db: AsyncSession,
    user_id: UUID,
    agent_id: UUID,
    project_id: Optional[UUID] = None,
    title: Optional[str] = None,
) -> AgentConversation:
    """
    Create a new conversation with an agent.
    
    Args:
        db: Database session
        user_id: ID of user starting the conversation
        agent_id: ID of the agent
        project_id: Optional project context
        title: Optional conversation title (auto-generated if not provided)
    
    Returns:
        Created AgentConversation
    """
    conversation = AgentConversation(
        agent_id=agent_id,
        user_id=user_id,
        project_id=project_id,
        title=title or "New Conversation",
        message_count=0,
    )
    
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    
    return conversation


async def add_message(
    db: AsyncSession,
    conversation_id: UUID,
    role: str,
    content: str,
    metadata: Optional[dict] = None,
) -> AgentMessage:
    """
    Add a message to a conversation.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation
        role: Message role ('user', 'assistant', 'system', 'tool')
        content: Message content
        metadata: Optional metadata (tool calls, citations, etc.)
    
    Returns:
        Created AgentMessage
    """
    message = AgentMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        message_metadata=metadata or {},
    )
    
    db.add(message)
    
    # Update conversation message count and updated_at
    result = await db.execute(
        select(AgentConversation).where(AgentConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if conversation:
        conversation.message_count += 1
        
        # Auto-generate title from first user message if not set
        if conversation.title == "New Conversation" and role == "user":
            # Use first 50 chars as title
            conversation.title = content[:50] + ("..." if len(content) > 50 else "")
    
    await db.commit()
    await db.refresh(message)
    
    return message


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    limit: Optional[int] = 100,
) -> List[AgentMessage]:
    """
    Get message history for a conversation.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation
        user_id: ID of the user (for permission check)
        limit: Maximum number of messages to return
    
    Returns:
        List of AgentMessage objects (oldest first)
    """
    # Check if user has access to this conversation
    result = await db.execute(
        select(AgentConversation).where(
            and_(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user_id
            )
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise ValueError("Conversation not found or access denied")
    
    # Get messages — fetch newest first so the limit keeps the most recent ones,
    # then reverse to return them in chronological order.
    query = (
        select(AgentMessage)
        .where(AgentMessage.conversation_id == conversation_id)
        .order_by(AgentMessage.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    messages = list(result.scalars().all())
    return list(reversed(messages))


async def list_conversations(
    db: AsyncSession,
    user_id: UUID,
    agent_id: Optional[UUID] = None,
    limit: int = 50,
) -> List[AgentConversation]:
    """
    List all conversations for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
        agent_id: Optional filter by agent
        limit: Maximum conversations to return
    
    Returns:
        List of AgentConversation objects (newest first)
    """
    query = select(AgentConversation).where(AgentConversation.user_id == user_id)
    
    if agent_id:
        query = query.where(AgentConversation.agent_id == agent_id)
    
    query = query.order_by(desc(AgentConversation.updated_at)).limit(limit)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_conversation_by_id(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
) -> Optional[AgentConversation]:
    """
    Get a conversation by ID.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation
        user_id: ID of the user (for permission check)
    
    Returns:
        AgentConversation if found and accessible, None otherwise
    """
    result = await db.execute(
        select(AgentConversation)
        .options(selectinload(AgentConversation.agent))
        .where(
            and_(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user_id
            )
        )
    )
    return result.scalar_one_or_none()


async def delete_conversation(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
) -> None:
    """
    Delete a conversation.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation
        user_id: ID of the user (for permission check)
    
    Raises:
        ValueError: If conversation not found or access denied
    """
    result = await db.execute(
        select(AgentConversation).where(
            and_(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user_id
            )
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise ValueError("Conversation not found or access denied")
    
    await db.delete(conversation)
    await db.commit()

    # Delete LangGraph checkpoint history for this conversation (thread_id = conversation_id)
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from app.agent.custom_agent_runner import _get_postgres_conn_string
    async with AsyncPostgresSaver.from_conn_string(_get_postgres_conn_string()) as checkpointer:
        await checkpointer.adelete_thread(str(conversation_id))


async def update_conversation_title(
    db: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    title: str,
) -> AgentConversation:
    """
    Update conversation title.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation
        user_id: ID of the user (for permission check)
        title: New title
    
    Returns:
        Updated AgentConversation
    """
    result = await db.execute(
        select(AgentConversation).where(
            and_(
                AgentConversation.id == conversation_id,
                AgentConversation.user_id == user_id
            )
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise ValueError("Conversation not found or access denied")
    
    conversation.title = title
    await db.commit()
    await db.refresh(conversation)
    
    return conversation
