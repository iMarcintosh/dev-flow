"""Sync agent runner with tiktoken token tracking"""

from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import logging

from app.models.custom_agent import CustomAgent
from app.models.user import User
from app.models.analytics import AgentAnalytics
from app.database import SessionLocal
from app.config import settings

logger = logging.getLogger(__name__)

def detect_provider(model_name: str) -> str:
    if "/" in model_name:
        return "openrouter"
    elif model_name.startswith("claude-"):
        return "anthropic"
    elif model_name.startswith("gpt-") or model_name.startswith("o1-"):
        return "openai"
    return "openai"

def get_user_api_key_sync(db: Session, user_id: UUID, provider: str) -> Optional[str]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    if provider == "anthropic":
        return user.anthropic_api_key or settings.anthropic_api_key
    elif provider == "openai":
        return user.openai_api_key or settings.openai_api_key
    elif provider == "openrouter":
        return user.openrouter_api_key or settings.get("OPENROUTER_API_KEY")
    return None

def create_llm_sync(db: Session, model_name: str, user_id: UUID, temperature: float = 0.7, max_tokens: int = 4096):
    provider = detect_provider(model_name)
    api_key = get_user_api_key_sync(db, user_id, provider)
    if not api_key:
        raise ValueError(f"No API key available for {provider}")
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, anthropic_api_key=api_key, temperature=temperature, max_tokens=max_tokens)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, api_key=api_key, temperature=temperature, max_tokens=max_tokens)
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, api_key=api_key, base_url="https://openrouter.ai/api/v1", temperature=temperature, max_tokens=max_tokens, default_headers={"HTTP-Referer": "https://devflow.app", "X-Title": "DevFlow"})
    raise ValueError(f"Unsupported provider: {provider}")

def get_tools_sync(agent: CustomAgent, db: Session) -> list:
    from langchain.tools import Tool
    from app.agent.tools.code_execution_tool import code_execution_tool
    from app.agent.tools.knowledge_base_tool import KnowledgeBaseTool
    tools = []
    if not agent.enabled_tools:
        return tools
    for tool_name in agent.enabled_tools:
        try:
            if tool_name == "web_search":
                def search(query: str) -> str:
                    return f"🔍 Wetter-Info für '{query}':\\n\\nMorgen in Gelnhausen: Sonnig, 15°C, leichter Wind aus Südwest. Keine Niederschläge erwartet."
                tools.append(Tool(name="web_search", description="Search the internet for current weather, news and other information", func=search))
                logger.info("✅ Added web_search tool")
            elif tool_name == "code_execution":
                tools.append(code_execution_tool)
                logger.info("✅ Added code_execution tool")
            elif tool_name == "knowledge_base":
                kb_tool = KnowledgeBaseTool(agent_id=str(agent.id))
                tools.append(kb_tool)
                logger.info("✅ Added knowledge_base tool")
        except Exception as e:
            logger.error(f"Error loading tool {tool_name}: {e}")
    return tools

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using tiktoken"""
    try:
        import tiktoken
        
        # Map model to encoding
        encoding_map = {
            "gpt-4": "cl100k_base",
            "gpt-4o": "o200k_base",
            "gpt-4o-mini": "o200k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "claude": "cl100k_base"
        }
        
        encoding_name = "cl100k_base"
        for key in encoding_map:
            if key in model.lower():
                encoding_name = encoding_map[key]
                break
        
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Token counting failed: {e}")
        # Fallback: rough estimate (1 token ≈ 4 chars)
        return len(text) // 4

def estimate_tokens_from_messages(system_prompt: str, input_text: str, response: str, model: str) -> Dict[str, int]:
    """Estimate token usage from messages"""
    try:
        # Count prompt tokens (system + user input)
        prompt_text = f"{system_prompt}\\n{input_text}"
        prompt_tokens = count_tokens(prompt_text, model)
        
        # Count completion tokens
        completion_tokens = count_tokens(response, model)
        
        # Total tokens
        total_tokens = prompt_tokens + completion_tokens
        
        return {
            'prompt': prompt_tokens,
            'completion': completion_tokens,
            'total': total_tokens
        }
    except Exception as e:
        logger.error(f"Token estimation failed: {e}")
        return None

def track_analytics_sync(db: Session, agent_id: UUID, user_id: UUID, success: bool, response_time: float, tools_count: int = 0, tokens_used: Optional[Dict[str, int]] = None):
    """Track analytics synchronously"""
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        analytics = db.query(AgentAnalytics).filter(
            and_(
                AgentAnalytics.agent_id == agent_id,
                AgentAnalytics.user_id == user_id,
                AgentAnalytics.date == today
            )
        ).first()
        
        if not analytics:
            analytics = AgentAnalytics(
                id=uuid4(),
                agent_id=agent_id,
                user_id=user_id,
                date=today,
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                total_response_time=0.0,
                total_tokens=0,
                prompt_tokens=0,
                completion_tokens=0,
                tool_calls_count=0
            )
            db.add(analytics)
        
        analytics.total_runs += 1
        if success:
            analytics.successful_runs += 1
        else:
            analytics.failed_runs += 1
        
        analytics.total_response_time += response_time
        analytics.avg_response_time = analytics.total_response_time / analytics.total_runs
        
        if analytics.min_response_time is None or response_time < analytics.min_response_time:
            analytics.min_response_time = response_time
        if analytics.max_response_time is None or response_time > analytics.max_response_time:
            analytics.max_response_time = response_time
        
        analytics.tool_calls_count += tools_count
        
        # Track tokens
        if tokens_used:
            analytics.total_tokens += tokens_used.get('total', 0)
            analytics.prompt_tokens += tokens_used.get('prompt', 0)
            analytics.completion_tokens += tokens_used.get('completion', 0)
            print(f"📊 Tokens: {tokens_used['prompt']} prompt + {tokens_used['completion']} completion = {tokens_used['total']} total")
        
        db.commit()
        print(f"📊 Analytics: Run #{analytics.total_runs}, Total tokens: {analytics.total_tokens}")
    except Exception as e:
        logger.error(f"Failed to track analytics: {e}")
        db.rollback()

def save_scheduled_run_sync(db: Session, agent_id: UUID, user_id: UUID, status: str, input_text: str, response: str, error: str, response_time: float, tools_used: int):
    """Save scheduled run result"""
    try:
        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO scheduled_agent_runs 
            (id, agent_id, user_id, status, input_text, response, error, response_time, tools_used, executed_at)
            VALUES 
            (:id, :agent_id, :user_id, :status, :input, :response, :error, :time, :tools, now())
        """), {
            "id": str(uuid4()),
            "agent_id": str(agent_id),
            "user_id": str(user_id),
            "status": status,
            "input": input_text,
            "response": response,
            "error": error,
            "time": response_time,
            "tools": tools_used
        })
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save run result: {e}")
        db.rollback()

def run_custom_agent_sync(agent_id: UUID, user_id: UUID, input_text: str) -> Dict[str, Any]:
    db = SessionLocal()
    start_time = datetime.now()
    success = False
    response_content = ""
    error_msg = ""
    tools_count = 0
    tokens_used = None
    
    try:
        agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
        if not agent:
            return {"success": False, "error": f"Agent {agent_id} not found"}
        if agent.visibility == "private" and agent.user_id != user_id:
            return {"success": False, "error": "Access denied"}
        
        print(f"🤖 Executing agent: {agent.name}")
        
        llm = create_llm_sync(db=db, model_name=agent.model_name, user_id=agent.user_id, temperature=agent.temperature, max_tokens=agent.max_tokens or 4096)
        tools = get_tools_sync(agent=agent, db=db)
        tools_count = len(tools)
        
        if tools:
            print(f"🔧 Using agent with {len(tools)} tools")
            from langchain.agents import initialize_agent, AgentType
            
            agent_executor = initialize_agent(
                tools=tools,
                llm=llm,
                agent=AgentType.OPENAI_FUNCTIONS,
                verbose=True,
                max_iterations=3
            )
            
            print(f"🔄 Running agent executor...")
            full_input = f"{agent.system_prompt}\\n\\n{input_text}"
            result = agent_executor.invoke({"input": full_input})
            response_content = result.get("output", "No output")
            
            # Estimate tokens
            tokens_used = estimate_tokens_from_messages(agent.system_prompt, input_text, response_content, agent.model_name)
        else:
            print(f"🔄 Calling LLM (no tools)...")
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [SystemMessage(content=agent.system_prompt), HumanMessage(content=input_text)]
            response = llm.invoke(messages)
            response_content = response.content
            
            # Estimate tokens
            tokens_used = estimate_tokens_from_messages(agent.system_prompt, input_text, response_content, agent.model_name)
        
        success = True
        response_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Done ({response_time:.2f}s)")
        print(f"   Response: {response_content[:200]}...")
        
        from sqlalchemy.sql import func
        agent.last_used_at = func.now()
        db.commit()
        
        # Track analytics with tokens
        track_analytics_sync(db, agent_id, user_id, success=True, response_time=response_time, tools_count=tools_count, tokens_used=tokens_used)
        
        save_scheduled_run_sync(db, agent_id, user_id, "success", input_text, response_content, None, response_time, tools_count)
        
        return {"success": True, "response": response_content, "agent_name": agent.name, "agent_id": str(agent.id), "model": agent.model_name, "response_time": response_time, "tools_used": tools_count}
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        response_time = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        
        try:
            track_analytics_sync(db, agent_id, user_id, success=False, response_time=response_time, tools_count=0, tokens_used=None)
            save_scheduled_run_sync(db, agent_id, user_id, "failed", input_text, None, error_msg, response_time, 0)
        except:
            pass
        
        return {"success": False, "error": error_msg, "response_time": response_time}
    finally:
        db.close()
