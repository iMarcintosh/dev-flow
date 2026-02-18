"""Model resolver for agents - detects provider and creates LLM instances."""

import logging
from typing import Optional
from app.config import settings
from app.database import async_session_maker
from sqlalchemy import select
from app.models.user import User

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


def create_llm(model_name: str, temperature: float = 0.7, max_tokens: int = 4096):
    """
    Create LLM instance based on detected provider.
    
    Args:
        model_name: Model identifier
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        LangChain LLM instance
        
    Raises:
        ValueError: If provider unknown or API key missing
    """
    provider = detect_provider(model_name)
    
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model_name,
            anthropic_api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            openai_api_key=settings.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    elif provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OpenRouter API key not configured")
        
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature,
            max_tokens=max_tokens,
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
    
    Args:
        user_id: UUID of the user
        agent_type: Type of agent
        temperature: Sampling temperature
        max_tokens: Max tokens
        
    Returns:
        LangChain LLM instance configured for the user
    """
    model_name = await get_user_model(user_id, agent_type)
    return create_llm(model_name, temperature, max_tokens)
