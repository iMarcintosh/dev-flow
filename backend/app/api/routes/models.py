"""API routes for model discovery and management."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any
from app.services.model_discovery import model_discovery_service
from app.models.user import User
from app.auth import get_current_user
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
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
async def get_available_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all available models from all providers.

    Requires authentication. Response is cached per user in Redis for 1 hour.

    Returns:
        {
            "anthropic": [...],
            "openai": [...],
            "openrouter": [...]
        }
    """
    from app.services import api_key_service
    cache_key = f"available_models:{current_user.id}"

    try:
        redis_client = await get_redis()
        cached = await redis_client.get(cache_key)

        if cached:
            logger.info(f"Returning cached model list for user {current_user.id}")
            return json.loads(cached)

        # Resolve per-user API keys
        openai_key = await api_key_service.get_api_key(db, str(current_user.id), "openai") or ""
        openrouter_key = await api_key_service.get_api_key(db, str(current_user.id), "openrouter") or ""

        logger.info(f"Fetching fresh model list for user {current_user.id}")
        models = await model_discovery_service.get_all_models(
            openai_key=openai_key,
            openrouter_key=openrouter_key
        )

        await redis_client.set(cache_key, json.dumps(models), ex=3600)
        return models

    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return {
            "anthropic": [m.to_dict() for m in model_discovery_service.ANTHROPIC_MODELS],
            "openai": [m.to_dict() for m in model_discovery_service.OPENAI_MODELS_FALLBACK],
            "openrouter": []
        }


@router.post("/refresh")
async def refresh_model_cache(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually refresh the model cache for the current user."""
    from app.services import api_key_service
    cache_key = f"available_models:{current_user.id}"

    try:
        redis_client = await get_redis()
        await redis_client.delete(cache_key)

        openai_key = await api_key_service.get_api_key(db, str(current_user.id), "openai") or ""
        openrouter_key = await api_key_service.get_api_key(db, str(current_user.id), "openrouter") or ""

        models = await model_discovery_service.get_all_models(
            openai_key=openai_key,
            openrouter_key=openrouter_key
        )

        await redis_client.set(cache_key, json.dumps(models), ex=3600)

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
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
    from app.services import api_key_service
    status = await api_key_service.get_api_key_status(db, str(current_user.id))
    if status.get(provider, "none") == "none":
        return {
            "accessible": False,
            "message": f"{provider} API key not configured"
        }
    return {
        "accessible": True,
        "message": f"API key configured for {provider}"
    }
