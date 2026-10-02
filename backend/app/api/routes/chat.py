"""Chat API endpoints."""

import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID
import uuid

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage
from app.agent.registry import registry
from app.agent.base_agent import AgentInput
from app.models.agent_run import AgentRun, AgentRunStatus
from app.api.routes.items import verify_project_access

logger = logging.getLogger(__name__)

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
    # Verify project access
    await verify_project_access(uuid.UUID(request.project_id), current_user, db)

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


@router.post("/stream")
async def send_chat_message_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream chat response as SSE."""
    # Verify project access before streaming
    await verify_project_access(uuid.UUID(request.project_id), current_user, db)

    agent = registry.get("chat_agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Chat agent not available")

    async def generate():
        try:
            yield f'data: {json.dumps({"type": "start"})}\n\n'

            # 1. Save user message immediately
            user_msg = ChatMessage(
                user_id=str(current_user.id),
                project_id=request.project_id,
                role="user",
                content=request.message,
            )
            db.add(user_msg)
            await db.commit()

            # 2. Get project context (stats + semantic search)
            from app.agent.memory.vector_store import vector_store
            stats = await vector_store.get_project_stats(db, request.project_id)
            relevant_items = await vector_store.similarity_search(
                db, request.message, request.project_id, top_k=15,
                api_key=current_user.openai_api_key
            )
            context = agent._build_context(stats, relevant_items)

            # 3. Get LLM
            llm = await agent._get_llm(str(current_user.id))
            if not llm:
                error_msg = "No LLM available. Please configure an API key in Settings."
                yield f'data: {json.dumps({"type": "stream", "content": error_msg})}\n\n'
                assistant_msg = ChatMessage(
                    user_id=str(current_user.id),
                    project_id=request.project_id,
                    role="assistant",
                    content=error_msg,
                )
                db.add(assistant_msg)
                await db.commit()
                yield f'data: {json.dumps({"type": "end"})}\n\n'
                return

            # 4. Stream via LangGraph checkpointer for conversation memory
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from langgraph.prebuilt import create_react_agent
            from langchain_core.messages import HumanMessage
            from app.agent.custom_agent_runner import _get_postgres_conn_string

            thread_id = f"board-{request.project_id}-{current_user.id}"

            system_prompt = f"""You are a helpful AI assistant for DevFlow, a project management tool.
You have access to the user's project board with all their tasks, bugs, stories, and epics.

{context}

CRITICAL RULES - NEVER VIOLATE THESE:
1. ONLY reference items that are EXPLICITLY listed in the "Relevant Items" section above
2. If no relevant items are found, say "I don't see any items matching that" - DO NOT make up items
3. NEVER invent item titles, descriptions, or details that aren't in the context
4. Use exact item titles from the context - do not paraphrase or change them
5. If you're unsure, say "I'm not certain" instead of guessing
6. When asked about counts, ONLY use the statistics provided in the context
7. ALWAYS respond in the SAME LANGUAGE the user asked in (German → German, English → English, etc.)

Guidelines:
- Be concise and helpful
- Reference specific items by their EXACT title in quotes when relevant
- Use the project statistics when answering questions about counts or status
- If you mention an item, format it like: "the bug 'Password field doesn't accept special characters'"
- Be conversational but professional
- If the context doesn't contain enough information to answer, explicitly say so

Remember: Accuracy is more important than being helpful. It's better to say "I don't have that information" than to make something up."""

            full_response = ""
            async with AsyncPostgresSaver.from_conn_string(_get_postgres_conn_string()) as checkpointer:
                await checkpointer.setup()
                agent_executor = create_react_agent(
                    llm,
                    tools=[],
                    prompt=system_prompt,
                    checkpointer=checkpointer,
                )
                async for event in agent_executor.astream(
                    {"messages": [HumanMessage(content=request.message)]},
                    stream_mode=["messages", "values"],
                    config={"configurable": {"thread_id": thread_id}},
                ):
                    mode, data = event
                    if mode != "messages":
                        continue
                    msg, metadata = data
                    from langchain_core.messages import AIMessageChunk
                    if isinstance(msg, AIMessageChunk) and msg.content:
                        full_response += msg.content
                        yield f'data: {json.dumps({"type": "stream", "content": msg.content})}\n\n'

            # 5. Save assistant message for frontend display
            assistant_msg = ChatMessage(
                user_id=str(current_user.id),
                project_id=request.project_id,
                role="assistant",
                content=full_response,
            )
            db.add(assistant_msg)
            await db.commit()

            yield f'data: {json.dumps({"type": "end"})}\n\n'

        except Exception as e:
            logger.exception("Error in chat stream")
            yield f'data: {json.dumps({"type": "error", "content": str(e)})}\n\n'
            yield f'data: {json.dumps({"type": "end"})}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history", response_model=List[ChatMessageResponse])
async def get_chat_history(
    project_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat history for a project."""
    await verify_project_access(uuid.UUID(project_id), current_user, db)

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


@router.delete("/history")
async def clear_chat_history(
    project_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear chat history for a project (DB messages + LangGraph checkpoint thread)."""
    await verify_project_access(project_id, current_user, db)

    from sqlalchemy import delete as sql_delete
    from app.agent.custom_agent_runner import _get_postgres_conn_string
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    # Delete DB messages for this user+project
    await db.execute(
        sql_delete(ChatMessage).where(
            and_(
                ChatMessage.project_id == str(project_id),
                ChatMessage.user_id == str(current_user.id),
            )
        )
    )
    await db.commit()

    # Delete LangGraph checkpoint thread
    thread_id = f"board-{project_id}-{current_user.id}"
    async with AsyncPostgresSaver.from_conn_string(_get_postgres_conn_string()) as checkpointer:
        await checkpointer.adelete_thread(thread_id)

    return {"success": True, "message": "Chat history cleared"}
