"""API routes for model discovery and management."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any
from app.services.model_discovery import model_discovery_service
from app.models.user import User
from app.auth import get_current_user
import redis.asyncio as redis
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/models", tags=["models"])

# Redis client for caching
_redis_client = None


async def get_redis():
    """Get Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return _redis_client


@router.get("")
async def get_available_models() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all available models from all providers.
    
    Response is cached in Redis for 1 hour.
    
    Returns:
        {
            "anthropic": [...],
            "openai": [...],
            "openrouter": [...]
        }
    """
    try:
        # Try to get from cache
        redis_client = await get_redis()
        cached = await redis_client.get("available_models")
        
        if cached:
            logger.info("Returning cached model list")
            return json.loads(cached)
        
        # Fetch fresh data
        logger.info("Fetching fresh model list from providers")
        models = await model_discovery_service.get_all_models()
        
        # Cache for 1 hour
        await redis_client.set(
            "available_models",
            json.dumps(models),
            ex=3600
        )
        
        return models
        
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        # Return fallback on error
        return {
            "anthropic": [m.to_dict() for m in model_discovery_service.ANTHROPIC_MODELS],
            "openai": [m.to_dict() for m in model_discovery_service.OPENAI_MODELS_FALLBACK],
            "openrouter": []
        }


@router.post("/refresh")
async def refresh_model_cache(current_user: User = Depends(get_current_user)):
    """
    Manually refresh the model cache.
    
    Requires authentication.
    """
    try:
        redis_client = await get_redis()
        
        # Delete cache
        await redis_client.delete("available_models")
        
        # Fetch fresh data
        models = await model_discovery_service.get_all_models()
        
        # Cache for 1 hour
        await redis_client.set(
            "available_models",
            json.dumps(models),
            ex=3600
        )
        
        return {
            "success": True,
            "message": "Model cache refreshed",
            "model_counts": {
                provider: len(models_list)
                for provider, models_list in models.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/{provider}/{model_name:path}")
async def test_model_access(
    provider: str,
    model_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Test if a specific model is accessible with current API keys.
    
    Args:
        provider: Provider name (anthropic, openai, openrouter)
        model_name: Model identifier
        
    Returns:
        {
            "accessible": true/false,
            "message": "Details"
        }
    """
    # Check if API key is configured
    if provider == "anthropic" and not settings.anthropic_api_key:
        return {
            "accessible": False,
            "message": "Anthropic API key not configured"
        }
    elif provider == "openai" and not settings.openai_api_key:
        return {
            "accessible": False,
            "message": "OpenAI API key not configured"
        }
    elif provider == "openrouter" and not settings.openrouter_api_key:
        return {
            "accessible": False,
            "message": "OpenRouter API key not configured"
        }
    
    # TODO: Actually test the model by making a minimal API call
    # For now, just check if key exists
    return {
        "accessible": True,
        "message": f"API key configured for {provider}"
    }
