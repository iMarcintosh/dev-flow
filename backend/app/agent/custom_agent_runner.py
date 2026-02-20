"""
Custom Agent Runner.

Executes custom agents configured by users with their specific
models, prompts, tools, and parameters.
"""

from typing import Optional, Dict, Any, AsyncGenerator, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import json

from app.models.custom_agent import CustomAgent
from app.agent.model_resolver import create_llm
from app.agent.tools.tool_registry import bind_tools_to_llm
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)


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
    
    # Note: Not setting top_p as both OpenAI and Anthropic reject
    # requests with both temperature AND top_p set
    
    # Bind tools if enabled
    if agent.enabled_tools:
        logger.info(f"🔧 Binding tools to LLM: {agent.enabled_tools}")

        from app.agent.tools.tool_registry import get_tools_list

        # Get tools list (exclude "mcp" — loaded separately below)
        tools = get_tools_list(
            tool_names=[t for t in agent.enabled_tools if t != "mcp"],
            db=db,
            user_id=str(user_id),
            project_id=str(project_id) if project_id else None,
            agent_id=str(agent_id),
        )

        # Async-load MCP tools if requested
        if "mcp" in agent.enabled_tools:
            from app.agent.tools.mcp_integration import get_mcp_tools
            mcp_configs = (agent.tool_config or {}).get("mcp", {}).get("servers", [])
            if mcp_configs:
                mcp_tools = await get_mcp_tools(mcp_configs)
                tools.extend(mcp_tools)
            else:
                logger.warning("⚠️ mcp tool enabled but no mcp_configs in tool_config")

        if tools:
            # All modern LLMs support bind_tools (OpenAI, Anthropic, etc.)
            llm = llm.bind_tools(tools)
            logger.info(f"✅ Tools bound using bind_tools() - {len(tools)} tools")
        else:
            logger.warning("⚠️ No tools to bind!")

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
    tools_list = []

    # Get tools list for execution (if enabled)
    if agent.enabled_tools:
        from app.agent.tools.tool_registry import get_tools_list
        tools_list = get_tools_list(
            tool_names=[t for t in agent.enabled_tools if t != "mcp"],
            db=db,
            user_id=str(user_id),
            project_id=str(project_id) if project_id else None,
            agent_id=str(agent_id),
        )
        # Async-load MCP tools for execution
        if "mcp" in agent.enabled_tools:
            from app.agent.tools.mcp_integration import get_mcp_tools
            mcp_configs = (agent.tool_config or {}).get("mcp", {}).get("servers", [])
            if mcp_configs:
                mcp_tools = await get_mcp_tools(mcp_configs)
                tools_list.extend(mcp_tools)
    
    try:
        # Phase 1: Initial LLM invocation (planning)
        logger.info(f"🤖 Phase 1: Calling LLM (planning)")
        response = await llm.ainvoke(messages)
        
        # Phase 2: Check if tool calls are requested
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"🔧 Phase 2: Tool calls detected: {len(response.tool_calls)}")
            
            # Add AI message with tool calls
            messages.append(AIMessage(
                content=response.content or "",
                tool_calls=response.tool_calls
            ))
            
            # Execute each tool call
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id")
                
                logger.info(f"  🛠️  Executing tool: {tool_name} with args: {tool_args}")
                
                try:
                    # Find tool in tools list
                    tool = _find_tool_by_name(tool_name, tools_list)
                    
                    if tool:
                        # Execute tool
                        tool_result = await tool.ainvoke(tool_args)
                        
                        # Convert result to string if needed
                        if isinstance(tool_result, dict):
                            result_str = json.dumps(tool_result)
                        else:
                            result_str = str(tool_result)
                        
                        logger.info(f"  ✅ Tool result: {result_str[:100]}...")
                        
                        # Add to tools_used tracking
                        tools_used.append(tool_name)
                        
                        # Add tool result message
                        messages.append(ToolMessage(
                            content=result_str,
                            tool_call_id=tool_id
                        ))
                    else:
                        error_msg = f"Tool '{tool_name}' not found in enabled tools"
                        logger.error(f"  ❌ {error_msg}")
                        messages.append(ToolMessage(
                            content=json.dumps({"error": error_msg}),
                            tool_call_id=tool_id
                        ))
                        
                except Exception as tool_error:
                    error_msg = f"Tool execution error: {str(tool_error)}"
                    logger.error(f"  ❌ {error_msg}")
                    messages.append(ToolMessage(
                        content=json.dumps({"error": error_msg}),
                        tool_call_id=tool_id
                    ))
            
            # Phase 3: Final LLM call with tool results
            logger.info(f"🎯 Phase 3: Calling LLM with tool results (finalization)")
            final_response = await llm.ainvoke(messages)
            response_content = final_response.content
            
        else:
            # No tool calls - use direct response
            logger.info(f"💬 No tool calls - using direct response")
            response_content = response.content
        
        success = True
        
        # Update usage stats
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
            "response": response_content,
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
    
    
    # Bind tools if enabled
    if agent.enabled_tools:
        from app.agent.tools.tool_registry import get_tools_list
        stream_tools = get_tools_list(
            tool_names=[t for t in agent.enabled_tools if t != "mcp"],
            db=db,
            user_id=str(user_id),
            project_id=str(project_id) if project_id else None,
            agent_id=str(agent_id),
        )
        if "mcp" in agent.enabled_tools:
            from app.agent.tools.mcp_integration import get_mcp_tools
            mcp_configs = (agent.tool_config or {}).get("mcp", {}).get("servers", [])
            if mcp_configs:
                mcp_tools = await get_mcp_tools(mcp_configs)
                stream_tools.extend(mcp_tools)
        if stream_tools:
            llm = llm.bind_tools(stream_tools)
    
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
        from sqlalchemy.sql import func
        agent.last_used_at = func.now()
        await db.commit()
        
    except Exception as e:
        yield f"\n\n❌ Error: {str(e)}"


async def run_custom_agent_sse(
    db: AsyncSession,
    agent_id: UUID,
    user_id: UUID,
    input_text: str,
    project_id: Optional[UUID] = None,
    conversation_id: Optional[UUID] = None,
) -> AsyncGenerator[str, None]:
    """
    Execute a custom agent with SSE streaming.

    Yields SSE-formatted strings with event types:
      {"type":"start"}
      {"type":"tool_call","name":"...","args":{...}}
      {"type":"tool_result","name":"...","duration_ms":...}
      {"type":"stream","content":"token"}
      {"type":"end","tools_used":[...],"model":"..."}
      {"type":"error","error":"..."}
    """
    # Load agent configuration
    result = await db.execute(
        select(CustomAgent).where(CustomAgent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        yield f'data: {json.dumps({"type": "error", "error": "Agent not found"})}\n\n'
        return

    if agent.visibility == "private" and agent.user_id != user_id:
        yield f'data: {json.dumps({"type": "error", "error": "Access denied"})}\n\n'
        return

    yield f'data: {json.dumps({"type": "start"})}\n\n'

    start_time = datetime.now()
    tools_used: List[str] = []

    try:
        # Create LLM
        llm = await create_llm(
            model_name=agent.model_name,
            user_id=user_id,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
        )

        # Get tools list
        tools_list: List[BaseTool] = []
        if agent.enabled_tools:
            from app.agent.tools.tool_registry import get_tools_list
            tools_list = get_tools_list(
                tool_names=[t for t in agent.enabled_tools if t != "mcp"],
                db=db,
                user_id=str(user_id),
                project_id=str(project_id) if project_id else None,
                agent_id=str(agent_id),
            )
            # Async-load MCP tools if requested
            if "mcp" in agent.enabled_tools:
                from app.agent.tools.mcp_integration import get_mcp_tools
                mcp_configs = (agent.tool_config or {}).get("mcp", {}).get("servers", [])
                if mcp_configs:
                    mcp_tools = await get_mcp_tools(mcp_configs)
                    tools_list.extend(mcp_tools)
                else:
                    logger.warning("⚠️ mcp tool enabled but no mcp_configs in tool_config")
        base_llm = llm  # unbound reference — used in Phase 3 to force text response
        if tools_list:
            llm = llm.bind_tools(tools_list)

        messages = [
            SystemMessage(content=agent.system_prompt),
            HumanMessage(content=input_text),
        ]

        # Phase 1: Initial LLM call — accumulate full response to detect tool calls
        logger.info("🤖 SSE Phase 1: Calling LLM")
        phase1_response = await llm.ainvoke(messages)

        # Phase 2: Execute tool calls if present
        if hasattr(phase1_response, 'tool_calls') and phase1_response.tool_calls:
            logger.info(f"🔧 SSE Phase 2: {len(phase1_response.tool_calls)} tool calls")

            messages.append(AIMessage(
                content=phase1_response.content or "",
                tool_calls=phase1_response.tool_calls,
            ))

            for tool_call in phase1_response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id")

                yield f'data: {json.dumps({"type": "tool_call", "name": tool_name, "args": tool_args})}\n\n'

                tool_start = datetime.now()
                try:
                    tool = _find_tool_by_name(tool_name, tools_list)
                    if tool:
                        tool_result = await tool.ainvoke(tool_args)
                        result_str = json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                        tools_used.append(tool_name)
                    else:
                        result_str = json.dumps({"error": f"Tool '{tool_name}' not found"})
                except Exception as tool_err:
                    result_str = json.dumps({"error": str(tool_err)})

                duration_ms = int((datetime.now() - tool_start).total_seconds() * 1000)
                yield f'data: {json.dumps({"type": "tool_result", "name": tool_name, "duration_ms": duration_ms})}\n\n'

                messages.append(ToolMessage(
                    content=result_str,
                    tool_call_id=tool_id,
                ))

        # Phase 3: Stream final response token by token
        logger.info("🎯 SSE Phase 3: Streaming final response")
        full_content = ""

        if tools_used:
            # After tool calls: use unbound LLM to force a text-only response (no tool calls possible)
            final_response = await base_llm.ainvoke(messages)
            full_content = final_response.content or ""
            if full_content:
                yield f'data: {json.dumps({"type": "stream", "content": full_content})}\n\n'
        else:
            # No tool calls: stream token by token as before
            async for chunk in llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    full_content += chunk.content
                    yield f'data: {json.dumps({"type": "stream", "content": chunk.content})}\n\n'

        # Persist to DB
        if conversation_id:
            from app.services import conversation_service
            await conversation_service.add_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=full_content,
                metadata={"model": agent.model_name, "tools_used": tools_used},
            )

        # Update usage stats
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
            tools_used=tools_used,
        )

        yield f'data: {json.dumps({"type": "end", "tools_used": tools_used, "model": agent.model_name})}\n\n'

    except Exception as e:
        logger.error(f"SSE agent error: {e}")
        # Track failed run
        response_time = (datetime.now() - start_time).total_seconds()
        try:
            from app.services.analytics import analytics_service
            await analytics_service.track_agent_run(
                db=db,
                agent_id=agent_id,
                user_id=user_id,
                success=False,
                response_time=response_time,
            )
        except Exception:
            pass
        yield f'data: {json.dumps({"type": "error", "error": str(e)})}\n\n'


def _find_tool_by_name(name: str, tools: List[BaseTool]) -> Optional[BaseTool]:
    """
    Find a tool by its name in the tools list.
    
    Args:
        name: Name of the tool to find
        tools: List of available tools
    
    Returns:
        The tool if found, None otherwise
    """
    for tool in tools:
        if tool.name == name:
            return tool
    return None
