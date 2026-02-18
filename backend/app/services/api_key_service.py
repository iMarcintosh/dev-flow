"""
API Key Service - Manages user API keys with encryption and fallback logic.

Handles:
- Storing encrypted API keys per user
- Retrieving keys with fallback to global .env keys
- Testing API key validity
- Deleting user keys
"""

import logging
from typing import Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.security.encryption import encrypt_api_key, decrypt_api_key, mask_api_key
from app.config import settings

logger = logging.getLogger(__name__)

ProviderType = Literal["anthropic", "openai", "openrouter"]


async def get_api_key(
    db: AsyncSession, 
    user_id: str, 
    provider: ProviderType
) -> Optional[str]:
    """
    Get API key for a user and provider with fallback to global .env key.
    
    Fallback hierarchy:
    1. User's encrypted API key (if set)
    2. Global .env API key (if set)
    3. None (no key available)
    
    Args:
        db: Database session
        user_id: User UUID
        provider: API provider (anthropic/openai/openrouter)
        
    Returns:
        Decrypted API key or None
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"User {user_id} not found")
        return None
    
    # Try user's key first
    user_key = None
    if provider == "anthropic":
        user_key = user.anthropic_api_key  # Property decrypts automatically
    elif provider == "openai":
        user_key = user.openai_api_key
    elif provider == "openrouter":
        user_key = user.openrouter_api_key
    
    if user_key:
        logger.debug(f"Using user's {provider} API key")
        return user_key
    
    # Fallback to global .env key
    global_key = None
    if provider == "anthropic":
        global_key = settings.anthropic_api_key
    elif provider == "openai":
        global_key = settings.openai_api_key
    elif provider == "openrouter":
        global_key = settings.openrouter_api_key
    
    if global_key:
        logger.debug(f"Using global {provider} API key (fallback)")
        return global_key
    
    logger.warning(f"No {provider} API key available for user {user_id}")
    return None


async def set_api_key(
    db: AsyncSession,
    user_id: str,
    provider: ProviderType,
    plain_key: str
) -> bool:
    """
    Encrypt and store an API key for a user.
    
    Args:
        db: Database session
        user_id: User UUID
        provider: API provider
        plain_key: Plain text API key to encrypt and store
        
    Returns:
        True if successful, False otherwise
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.error(f"User {user_id} not found")
        return False
    
    # Encrypt key
    encrypted = encrypt_api_key(plain_key)
    if not encrypted:
        logger.error(f"Failed to encrypt {provider} API key")
        return False
    
    # Store encrypted key
    try:
        if provider == "anthropic":
            user.encrypted_anthropic_key = encrypted
        elif provider == "openai":
            user.encrypted_openai_key = encrypted
        elif provider == "openrouter":
            user.encrypted_openrouter_key = encrypted
        
        await db.commit()
        logger.info(f"Stored {provider} API key for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store {provider} API key: {e}")
        await db.rollback()
        return False


async def delete_api_key(
    db: AsyncSession,
    user_id: str,
    provider: ProviderType
) -> bool:
    """
    Delete a user's API key (will fallback to global .env key).
    
    Args:
        db: Database session
        user_id: User UUID
        provider: API provider
        
    Returns:
        True if successful, False otherwise
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.error(f"User {user_id} not found")
        return False
    
    try:
        if provider == "anthropic":
            user.encrypted_anthropic_key = None
        elif provider == "openai":
            user.encrypted_openai_key = None
        elif provider == "openrouter":
            user.encrypted_openrouter_key = None
        
        await db.commit()
        logger.info(f"Deleted {provider} API key for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete {provider} API key: {e}")
        await db.rollback()
        return False


async def get_api_key_status(
    db: AsyncSession,
    user_id: str
) -> dict[str, Literal["personal", "global", "none"]]:
    """
    Get the status of API keys for all providers.
    
    Returns which source each provider's key comes from:
    - "personal": User has their own key set
    - "global": Using global .env fallback key
    - "none": No key available
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        Dict with status for each provider
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return {
            "anthropic": "none",
            "openai": "none",
            "openrouter": "none"
        }
    
    status = {}
    
    # Check each provider
    for provider in ["anthropic", "openai", "openrouter"]:
        # Check user key
        has_user_key = False
        if provider == "anthropic":
            has_user_key = bool(user.encrypted_anthropic_key)
        elif provider == "openai":
            has_user_key = bool(user.encrypted_openai_key)
        elif provider == "openrouter":
            has_user_key = bool(user.encrypted_openrouter_key)
        
        if has_user_key:
            status[provider] = "personal"
            continue
        
        # Check global key
        has_global_key = False
        if provider == "anthropic":
            has_global_key = bool(settings.anthropic_api_key)
        elif provider == "openai":
            has_global_key = bool(settings.openai_api_key)
        elif provider == "openrouter":
            has_global_key = bool(settings.openrouter_api_key)
        
        status[provider] = "global" if has_global_key else "none"
    
    return status


async def test_api_key(provider: ProviderType, api_key: str) -> tuple[bool, Optional[str]]:
    """
    Test if an API key is valid by making a minimal API call.
    
    Args:
        provider: API provider
        api_key: Plain text API key to test
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model="claude-3-haiku-20240307",
                anthropic_api_key=api_key,
                max_tokens=10
            )
            # Simple test message
            llm.invoke("Hi")
            return (True, None)
            
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_key=api_key,
                max_tokens=10
            )
            llm.invoke("Hi")
            return (True, None)
            
        elif provider == "openrouter":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="anthropic/claude-3-haiku",
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                max_tokens=10
            )
            llm.invoke("Hi")
            return (True, None)
        
        return (False, f"Unknown provider: {provider}")
        
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"API key test failed for {provider}: {error_msg}")
        
        # Parse common errors
        if "401" in error_msg or "authentication" in error_msg.lower():
            return (False, "Invalid API key (authentication failed)")
        elif "403" in error_msg:
            return (False, "API key lacks required permissions")
        elif "429" in error_msg:
            return (False, "Rate limit exceeded (try again later)")
        else:
            return (False, f"API error: {error_msg[:100]}")
