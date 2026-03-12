"""Model resolver for agents - detects provider and creates LLM instances with user API keys."""

import logging
from typing import Optional
from app.config import settings
from app.database import async_session_maker
from sqlalchemy import select
from app.models.user import User
from app.services import api_key_service

logger = logging.getLogger(__name__)


def detect_provider(model_name: str) -> str:
    """
    Detect provider from model name.
    
    Examples:
        "claude-3-haiku-20240307" → "anthropic"
        "gpt-4-turbo" → "openai"
        "anthropic/claude-3-5-sonnet" → "openrouter"
        "meta-llama/llama-3-70b" → "openrouter"
    """
    if "/" in model_name:
        return "openrouter"
    elif model_name.startswith("claude-"):
        return "anthropic"
    elif model_name.startswith("gpt-"):
        return "openai"
    elif model_name.startswith("gemini-"):
        return "google"
    else:
        raise ValueError(f"Unknown model: {model_name}")


async def create_llm(model_name: str, user_id: str, temperature: float = 0.7, max_tokens: int = 4096):
    """
    Create LLM instance based on detected provider using user's API key.
    
    Falls back to global .env key if user hasn't set a personal key.
    
    Args:
        model_name: Model identifier
        user_id: User UUID to get API key for
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        LangChain LLM instance
        
    Raises:
        ValueError: If provider unknown or no API key available
    """
    provider = detect_provider(model_name)
    
    # Get user's API key (or fallback to global)
    async with async_session_maker() as db:
        api_key = await api_key_service.get_api_key(db, user_id, provider)
    
    if not api_key:
        raise ValueError(f"No API key available for {provider} (user {user_id})")
    
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_name,
            anthropic_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30
        )

    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30,
            default_headers={
                "HTTP-Referer": "https://devflow.app",
                "X-Title": "DevFlow"
            }
        )
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")


async def get_user_model(user_id: str, agent_type: str) -> str:
    """
    Get user's preferred model for a specific agent type.
    
    Args:
        user_id: UUID of the user
        agent_type: Type of agent (task_creator, chat_agent, daily_summary)
        
    Returns:
        Model name (e.g., "claude-3-haiku-20240307")
        Falls back to default if not set.
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user or not user.preferred_models:
                # Default fallback
                return "claude-3-haiku-20240307"
            
            # Get model for this agent type
            model = user.preferred_models.get(agent_type)
            
            if not model:
                # Fallback to default
                return "claude-3-haiku-20240307"
            
            return model
            
    except Exception as e:
        logger.error(f"Error fetching user model: {e}")
        return "claude-3-haiku-20240307"


async def get_user_llm(user_id: str, agent_type: str, temperature: float = 0.7, max_tokens: int = 4096):
    """
    Convenience function to get LLM instance for a user and agent type.
    
    Uses user's preferred model and API key (with fallback to global keys).
    
    Args:
        user_id: UUID of the user
        agent_type: Type of agent
        temperature: Sampling temperature
        max_tokens: Max tokens
        
    Returns:
        LangChain LLM instance configured for the user
    """
    model_name = await get_user_model(user_id, agent_type)
    return await create_llm(model_name, user_id, temperature, max_tokens)
