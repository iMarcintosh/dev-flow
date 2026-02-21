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

from langgraph.prebuilt import create_react_agent
from langgraph.errors import GraphRecursionError
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage, AIMessageChunk

from app.models.custom_agent import CustomAgent
from app.agent.model_resolver import create_llm
from app.agent.tools.tool_registry import bind_tools_to_llm
from app.agent.utils import _collect_token_usage
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

_LANGGRAPH_RECURSION_MSG = "Sorry, need more steps to process this request."


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
        # Build LangGraph agent (tools are bound internally)
        agent_executor = create_react_agent(llm, tools=tools_list)

        logger.info(f"🤖 Invoking LangGraph agent")
        result = await agent_executor.ainvoke(
            {
                "messages": [
                    SystemMessage(content=agent.system_prompt),
                    HumanMessage(content=input_text),
                ]
            },
            config={"recursion_limit": 10},
        )

        # Extract last AI message as the final response
        last_ai_msg = next(
            (m for m in reversed(result["messages"]) if isinstance(m, AIMessage)),
            None,
        )
        response_content = _extract_text_content(last_ai_msg.content) if last_ai_msg else ""

        # Collect tool names from message history
        tools_used = [
            m.name
            for m in result["messages"]
            if isinstance(m, ToolMessage) and getattr(m, "name", None)
        ]

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
        # Build LangGraph agent — tools are bound internally, pass unbound LLM
        agent_executor = create_react_agent(llm, tools=tools_list)

        messages_input = [
            SystemMessage(content=agent.system_prompt),
            HumanMessage(content=input_text),
        ]

        logger.info("🤖 SSE: Starting LangGraph agent stream")
        full_content = ""
        # tool_call_chunks accumulator: id -> {name, args_str, start_time}
        pending_tool_calls: dict = {}
        # Track ToolMessage IDs already emitted to suppress duplicate chunks
        emitted_tool_results: set = set()
        # Track the final state to extract the complete AI response after tool calls
        final_state_messages: list = []

        async for event in agent_executor.astream(
            {"messages": messages_input},
            stream_mode=["messages", "values"],
            config={"recursion_limit": 10},
        ):
            mode, data = event

            if mode == "values":
                # State snapshot — keep the latest for final answer extraction
                final_state_messages = data.get("messages", [])
                continue

            # mode == "messages": data is (msg, metadata)
            msg, metadata = data

            if isinstance(msg, AIMessageChunk):
                # Accumulate tool-call chunks (name + args arrive in separate chunks)
                if msg.tool_call_chunks:
                    for chunk in msg.tool_call_chunks:
                        # Use index as stable key — id only appears in the first chunk
                        idx = str(chunk.get("index", "0"))
                        tool_id = chunk.get("id") or ""
                        name = chunk.get("name") or ""
                        args_str = chunk.get("args") or ""

                        if idx not in pending_tool_calls:
                            pending_tool_calls[idx] = {
                                "tool_id": tool_id,
                                "name": name,
                                "args_str": args_str,
                                "start_time": datetime.now(),
                            }
                        else:
                            if tool_id:
                                pending_tool_calls[idx]["tool_id"] = tool_id
                            if name:
                                pending_tool_calls[idx]["name"] = name
                            pending_tool_calls[idx]["args_str"] += args_str

                # Final text stream (no tool calls in this chunk)
                elif msg.content:
                    text = _extract_text_content(msg.content)
                    if text:
                        full_content += text
                        yield f'data: {json.dumps({"type": "stream", "content": text})}\n\n'

            elif isinstance(msg, ToolMessage):
                tool_call_id = getattr(msg, "tool_call_id", None) or ""
                # Suppress duplicate ToolMessage chunks for the same call
                if tool_call_id in emitted_tool_results:
                    continue
                emitted_tool_results.add(tool_call_id)

                # Find the pending entry whose tool_id matches this ToolMessage's tool_call_id
                matched_idx = next(
                    (idx for idx, info in pending_tool_calls.items()
                     if info["tool_id"] == tool_call_id),
                    None,
                )
                if matched_idx is not None:
                    info = pending_tool_calls.pop(matched_idx)
                    tool_name = info["name"] or getattr(msg, "name", None) or "unknown"
                    try:
                        args_parsed = json.loads(info["args_str"]) if info["args_str"] else {}
                    except Exception:
                        args_parsed = {}
                    duration_ms = int((datetime.now() - info["start_time"]).total_seconds() * 1000)
                    yield f'data: {json.dumps({"type": "tool_call", "name": tool_name, "args": args_parsed})}\n\n'
                else:
                    tool_name = getattr(msg, "name", None) or "unknown"
                    duration_ms = 0

                if tool_name not in tools_used:
                    tools_used.append(tool_name)
                yield f'data: {json.dumps({"type": "tool_result", "name": tool_name, "duration_ms": duration_ms})}\n\n'

        # Extract final answer from the state snapshot if stream missed it
        # This happens when the last AI response after tool calls comes as a complete AIMessage
        # rather than streaming AIMessageChunk events
        from langchain_core.messages import AIMessage as LCAIMessage
        if final_state_messages:
            last_msg = final_state_messages[-1]
            if isinstance(last_msg, LCAIMessage):
                final_text = _extract_text_content(last_msg.content) if last_msg.content else ""
                if _LANGGRAPH_RECURSION_MSG in final_text:
                    logger.warning("⚠️ Agent hit recursion limit (detected in final state)")
                    user_msg = ("Der Agent hat das maximale Limit an Tool-Aufrufen erreicht. "
                                "Bitte stelle eine spezifischere Frage.")
                    yield f'data: {json.dumps({"type": "stream", "content": user_msg})}\n\n'
                    full_content = (full_content + "\n\n" + user_msg).strip() if full_content else user_msg
                else:
                    if final_text and final_text != full_content:
                        # The final answer is more complete than what was streamed
                        if final_text.startswith(full_content):
                            # Append only the missing suffix
                            additional = final_text[len(full_content):]
                        else:
                            # Completely different — use the full final text
                            additional = final_text
                        if additional:
                            yield f'data: {json.dumps({"type": "stream", "content": additional})}\n\n'
                        full_content = final_text

        logger.info(f"🤖 SSE: Stream complete, full_content length={len(full_content)}")

        # Collect real token usage from all AIMessage turns
        tokens_used = _collect_token_usage(final_state_messages)

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
            tokens_used=tokens_used,
        )

        yield f'data: {json.dumps({"type": "end", "tools_used": tools_used, "model": agent.model_name})}\n\n'

    except GraphRecursionError:
        logger.warning("⚠️ Agent hit GraphRecursionError")
        user_msg = ("Der Agent hat das maximale Limit an Tool-Aufrufen erreicht. "
                    "Bitte stelle eine spezifischere Frage.")
        suffix = ("\n\n" + user_msg) if full_content else user_msg
        full_content = (full_content + suffix).strip()
        yield f'data: {json.dumps({"type": "stream", "content": suffix.strip()})}\n\n'
        if conversation_id:
            from app.services import conversation_service
            await conversation_service.add_message(
                db=db, conversation_id=conversation_id, role="assistant",
                content=full_content,
                metadata={"model": agent.model_name, "tools_used": tools_used},
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
    """Find a tool by its name in the tools list."""
    for tool in tools:
        if tool.name == name:
            return tool
    return None


def _extract_text_content(content) -> str:
    """Extract plain text from LLM content — handles str and Anthropic list format."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return ''.join(
            block.get('text', '') if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content) if content else ''
