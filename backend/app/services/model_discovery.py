"""Model discovery service for fetching available LLM models from providers."""

import logging
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class ModelInfo:
    """Information about an LLM model."""
    
    def __init__(
        self,
        id: str,
        name: str,
        provider: str,
        description: str = "",
        context_window: int = 0,
        cost_tier: str = "unknown",
        pricing: Optional[Dict[str, str]] = None
    ):
        self.id = id
        self.name = name
        self.provider = provider
        self.description = description
        self.context_window = context_window
        self.cost_tier = cost_tier
        self.pricing = pricing or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "description": self.description,
            "context_window": self.context_window,
            "cost_tier": self.cost_tier,
            "pricing": self.pricing
        }


class ModelDiscoveryService:
    """Service for discovering available models from various providers."""
    
    # Hardcoded fallback lists (updated Feb 2026 from official docs)
    ANTHROPIC_MODELS = [
        ModelInfo(
            id="claude-opus-4-6",
            name="Claude Opus 4.6",
            provider="anthropic",
            description="The most intelligent model for building agents and coding",
            context_window=200000,
            cost_tier="highest"
        ),
        ModelInfo(
            id="claude-sonnet-4-6",
            name="Claude Sonnet 4.6",
            provider="anthropic",
            description="The best combination of speed and intelligence",
            context_window=200000,
            cost_tier="high"
        ),
        ModelInfo(
            id="claude-haiku-4-5",
            name="Claude Haiku 4.5",
            provider="anthropic",
            description="The fastest model with near-frontier intelligence",
            context_window=200000,
            cost_tier="low"
        ),
        ModelInfo(
            id="claude-sonnet-4-5",
            name="Claude Sonnet 4.5",
            provider="anthropic",
            description="Previous version of Sonnet",
            context_window=200000,
            cost_tier="high"
        ),
        ModelInfo(
            id="claude-opus-4-5",
            name="Claude Opus 4.5",
            provider="anthropic",
            description="Previous version of Opus",
            context_window=200000,
            cost_tier="highest"
        ),
        ModelInfo(
            id="claude-opus-4-1",
            name="Claude Opus 4.1",
            provider="anthropic",
            description="Older Opus version",
            context_window=200000,
            cost_tier="highest"
        ),
        ModelInfo(
            id="claude-sonnet-4-0",
            name="Claude Sonnet 4.0",
            provider="anthropic",
            description="Older Sonnet version",
            context_window=200000,
            cost_tier="high"
        ),
        ModelInfo(
            id="claude-3-7-sonnet-latest",
            name="Claude 3.7 Sonnet (Latest)",
            provider="anthropic",
            description="Latest Claude 3.7 model",
            context_window=200000,
            cost_tier="high"
        ),
        ModelInfo(
            id="claude-opus-4-0",
            name="Claude Opus 4.0",
            provider="anthropic",
            description="First Claude 4 Opus",
            context_window=200000,
            cost_tier="highest"
        ),
        # Legacy models (still available)
        ModelInfo(
            id="claude-3-haiku-20240307",
            name="Claude 3 Haiku",
            provider="anthropic",
            description="Fastest model, great for chat and simple tasks",
            context_window=200000,
            cost_tier="low"
        ),
    ]
    
    OPENAI_MODELS_FALLBACK = [
        # GPT-4.1 family (current, 2025)
        ModelInfo(
            id="gpt-4.1",
            name="GPT-4.1",
            provider="openai",
            description="Most capable GPT-4.1, great for text and analysis",
            context_window=1000000,
            cost_tier="high"
        ),
        ModelInfo(
            id="gpt-4.1-mini",
            name="GPT-4.1 Mini",
            provider="openai",
            description="Smaller, faster GPT-4.1 variant",
            context_window=1000000,
            cost_tier="medium"
        ),
        ModelInfo(
            id="gpt-4.1-nano",
            name="GPT-4.1 Nano",
            provider="openai",
            description="Smallest and cheapest GPT-4.1 variant",
            context_window=1000000,
            cost_tier="low"
        ),
        # GPT-4o (still available)
        ModelInfo(
            id="gpt-4o",
            name="GPT-4o",
            provider="openai",
            description="GPT-4o multimodal model",
            context_window=128000,
            cost_tier="high"
        ),
        ModelInfo(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            provider="openai",
            description="Fast and affordable GPT-4o variant",
            context_window=128000,
            cost_tier="low"
        ),
    ]
    
    async def fetch_anthropic_models(self) -> List[ModelInfo]:
        """
        Fetch Anthropic models.
        
        Note: Anthropic doesn't provide a public /models endpoint,
        so we use the hardcoded list.
        """
        return self.ANTHROPIC_MODELS
    
    async def fetch_openai_models(self) -> List[ModelInfo]:
        """Fetch OpenAI models from API."""
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured, using fallback list")
            return self.OPENAI_MODELS_FALLBACK
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"}
                )
                response.raise_for_status()
                data = response.json()
            
            # Filter to chat models only
            models = []
            chat_model_prefixes = ("gpt-4", "gpt-3.5-turbo", "gpt-5", "o1", "o3")
            
            for model in data.get("data", []):
                model_id = model.get("id", "")
                if model_id.startswith(chat_model_prefixes):
                    # Map to ModelInfo
                    name = model_id.replace("-", " ").title()
                    tier = "high" if "gpt-4" in model_id else "low"
                    
                    models.append(ModelInfo(
                        id=model_id,
                        name=name,
                        provider="openai",
                        description=f"OpenAI {name}",
                        context_window=0,  # Not provided by API
                        cost_tier=tier
                    ))
            
            return models if models else self.OPENAI_MODELS_FALLBACK
            
        except Exception as e:
            logger.error(f"Failed to fetch OpenAI models: {e}")
            return self.OPENAI_MODELS_FALLBACK
    
    async def fetch_openrouter_models(self) -> List[ModelInfo]:
        """Fetch models from OpenRouter API."""
        if not settings.openrouter_api_key:
            logger.warning("OpenRouter API key not configured")
            return []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {settings.openrouter_api_key}"}
                )
                response.raise_for_status()
                data = response.json()
            
            models = []
            for model in data.get("data", []):
                model_id = model.get("id", "")
                pricing = model.get("pricing", {})
                context_length = model.get("context_length", 0)
                
                # Extract provider from id (e.g., "anthropic/claude-3-opus" -> "anthropic")
                provider = model_id.split("/")[0] if "/" in model_id else "openrouter"
                
                # Determine cost tier from pricing
                prompt_price = float(pricing.get("prompt", "0"))
                if prompt_price == 0:
                    tier = "free"
                elif prompt_price < 0.000001:  # < $1 per 1M tokens
                    tier = "low"
                elif prompt_price < 0.000005:  # < $5 per 1M tokens
                    tier = "medium"
                else:
                    tier = "high"
                
                models.append(ModelInfo(
                    id=model_id,
                    name=model.get("name", model_id),
                    provider="openrouter",
                    description=model.get("description", ""),
                    context_window=context_length,
                    cost_tier=tier,
                    pricing={
                        "prompt": pricing.get("prompt"),
                        "completion": pricing.get("completion")
                    }
                ))
            
            return models
            
        except Exception as e:
            logger.error(f"Failed to fetch OpenRouter models: {e}")
            return []
    
    async def get_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetch models from all providers.
        
        Returns:
            Dictionary grouped by provider:
            {
                "anthropic": [model1, model2, ...],
                "openai": [model1, model2, ...],
                "openrouter": [model1, model2, ...]
            }
        """
        anthropic_models = await self.fetch_anthropic_models()
        openai_models = await self.fetch_openai_models()
        openrouter_models = await self.fetch_openrouter_models()
        
        return {
            "anthropic": [m.to_dict() for m in anthropic_models],
            "openai": [m.to_dict() for m in openai_models],
            "openrouter": [m.to_dict() for m in openrouter_models]
        }


# Singleton instance
model_discovery_service = ModelDiscoveryService()
