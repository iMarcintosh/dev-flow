"""
Custom Agent Runner.

Executes custom agents configured by users with their specific
models, prompts, tools, and parameters.
"""

from typing import Optional, Dict, Any, AsyncGenerator
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.custom_agent import CustomAgent
from app.agent.model_resolver import create_llm
from app.agent.tools.tool_registry import bind_tools_to_llm
from langchain_core.messages import HumanMessage, SystemMessage


async def run_custom_agent(
    db: AsyncSession,
    agent_id: UUID,
    user_id: UUID,
    input_text: str,
    project_id: Optional[UUID] = None,
    conversation_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Execute a custom agent.
    
    Args:
        db: Database session
        agent_id: ID of the custom agent to run
        user_id: ID of the user running the agent
        input_text: User's input message
        project_id: Optional project context for board tools
        conversation_id: Optional conversation ID for context
    
    Returns:
        Dict with agent response and metadata
    """
    # Load agent configuration
    result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")
    
    # Check access permissions
    if agent.visibility == "private" and agent.user_id != user_id:
        raise ValueError("Access denied to private agent")
    
    # Create LLM with agent's configuration
    llm = await create_llm(
        model_name=agent.model_name,
        user_id=user_id,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
    )
    
    # Apply additional parameters (only for compatible providers)
    # OpenAI doesn't support both temperature AND top_p
    if hasattr(llm, 'top_p') and not agent.model_name.startswith('gpt-'):
        llm.top_p = agent.top_p
    
    # Bind tools if enabled
    if agent.enabled_tools:
        llm = bind_tools_to_llm(
            llm=llm,
            tool_names=agent.enabled_tools,
            db=db,
            user_id=str(user_id),
            project_id=str(project_id) if project_id else None,
            agent_id=str(agent_id),  # Pass agent_id for knowledge_base tool
        )
    
    # Create messages with system prompt
    messages = [
        SystemMessage(content=agent.system_prompt),
        HumanMessage(content=input_text),
    ]
    
    # TODO: Add conversation history if conversation_id provided
    
    # Execute agent
    start_time = datetime.now()
    success = False
    tools_used = []
    
    try:
        response = await llm.ainvoke(messages)
        success = True
        
        # Update usage stats
        agent.run_count += 1
        from sqlalchemy.sql import func
        agent.last_used_at = func.now()
        await db.commit()
        
        # Track analytics
        response_time = (datetime.now() - start_time).total_seconds()
        from app.services.analytics import analytics_service
        await analytics_service.track_agent_run(
            db=db,
            agent_id=agent_id,
            user_id=user_id,
            success=True,
            response_time=response_time,
            tools_used=tools_used
        )
        
        return {
            "success": True,
            "response": response.content,
            "agent_name": agent.name,
            "agent_id": str(agent.id),
            "model": agent.model_name,
            "tools_used": tools_used,
        }
    
    except Exception as e:
        # Track failed run
        response_time = (datetime.now() - start_time).total_seconds()
        from app.services.analytics import analytics_service
        await analytics_service.track_agent_run(
            db=db,
            agent_id=agent_id,
            user_id=user_id,
            success=False,
            response_time=response_time
        )
        
        return {
            "success": False,
            "error": str(e),
            "agent_name": agent.name,
            "agent_id": str(agent.id),
        }


async def test_agent(
    db: AsyncSession,
    agent_id: UUID,
    user_id: UUID,
    test_input: str = "Hello! Please introduce yourself and describe what you can help with.",
) -> Dict[str, Any]:
    """
    Test an agent with a simple prompt.
    
    Useful for validating agent configuration before saving.
    
    Args:
        db: Database session
        agent_id: ID of agent to test
        user_id: ID of user testing
        test_input: Test prompt
    
    Returns:
        Dict with test results
    """
    return await run_custom_agent(
        db=db,
        agent_id=agent_id,
        user_id=user_id,
        input_text=test_input,
    )


async def run_custom_agent_streaming(
    db: AsyncSession,
    agent_id: UUID,
    user_id: UUID,
    input_text: str,
    project_id: Optional[UUID] = None,
    conversation_id: Optional[UUID] = None,
) -> AsyncGenerator[str, None]:
    """
    Execute a custom agent with streaming responses.
    
    Args:
        db: Database session
        agent_id: ID of the custom agent to run
        user_id: ID of the user running the agent
        input_text: User's input message
        project_id: Optional project context for board tools
        conversation_id: Optional conversation ID for context
    
    Yields:
        Chunks of the agent's response
    """
    # Load agent configuration
    result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")
    
    # Check access permissions
    if agent.visibility == "private" and agent.user_id != user_id:
        raise ValueError("Access denied to private agent")
    
    # Create LLM with agent's configuration
    llm = await create_llm(
        model_name=agent.model_name,
        user_id=user_id,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
    )
    
    # Apply additional parameters (only for compatible providers)
    # OpenAI doesn't support both temperature AND top_p
    if hasattr(llm, 'top_p') and not agent.model_name.startswith('gpt-'):
        llm.top_p = agent.top_p
    
    # Bind tools if enabled
    if agent.enabled_tools:
        llm = bind_tools_to_llm(
            llm=llm,
            tool_names=agent.enabled_tools,
            db=db,
            user_id=str(user_id),
            project_id=str(project_id) if project_id else None,
            agent_id=str(agent_id),
        )
    
    # Create messages with system prompt
    messages = [
        SystemMessage(content=agent.system_prompt),
        HumanMessage(content=input_text),
    ]
    
    # Stream agent response
    try:
        async for chunk in llm.astream(messages):
            if hasattr(chunk, 'content'):
                content = chunk.content
                if content:
                    yield content
        
        # Update usage stats
        agent.run_count += 1
        from sqlalchemy.sql import func
        agent.last_used_at = func.now()
        await db.commit()
        
    except Exception as e:
        yield f"\n\n❌ Error: {str(e)}"
