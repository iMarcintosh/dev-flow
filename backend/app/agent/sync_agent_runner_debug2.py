"""DEBUG version 2 - inspect full response"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import json

from app.models.custom_agent import CustomAgent
from app.models.user import User
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
    else:
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
                    return f"🔍 Web search for {query} - Feature coming soon"
                tools.append(Tool(name="web_search", description="Search the internet for current information", func=search))
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

def run_custom_agent_sync(agent_id: UUID, user_id: UUID, input_text: str) -> Dict[str, Any]:
    db = SessionLocal()
    start_time = datetime.now()
    try:
        agent = db.query(CustomAgent).filter(CustomAgent.id == agent_id).first()
        if not agent:
            return {"success": False, "error": f"Agent {agent_id} not found"}
        if agent.visibility == "private" and agent.user_id != user_id:
            return {"success": False, "error": "Access denied"}
        
        print(f"🤖 Executing agent: {agent.name}")
        llm = create_llm_sync(db=db, model_name=agent.model_name, user_id=agent.user_id, temperature=agent.temperature, max_tokens=agent.max_tokens or 4096)
        tools = get_tools_sync(agent=agent, db=db)
        
        if tools:
            print(f"🔧 Binding {len(tools)} tools")
            llm = llm.bind_tools(tools)
        
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [SystemMessage(content=agent.system_prompt), HumanMessage(content=input_text)]
        
        print("🔄 Calling LLM...")
        response = llm.invoke(messages)
        
        # FULL DEBUG
        print(f"🔍 Response.__dict__:")
        for key, val in response.__dict__.items():
            print(f"   {key}: {val}")
        
        print(f"🔍 Response.content: [{response.content}]")
        print(f"🔍 Response.additional_kwargs: {response.additional_kwargs}")
        
        response_content = response.content or "No response content"
        response_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Done ({response_time:.2f}s)")
        
        from sqlalchemy.sql import func
        agent.last_used_at = func.now()
        db.commit()
        
        return {"success": True, "response": response_content, "agent_name": agent.name, "agent_id": str(agent.id), "model": agent.model_name, "response_time": response_time}
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "response_time": (datetime.now() - start_time).total_seconds()}
    finally:
        db.close()
