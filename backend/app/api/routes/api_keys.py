"""API endpoints for managing user API keys."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Literal

from app.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.services import api_key_service
from app.security.encryption import mask_api_key

router = APIRouter(prefix="/api/api-keys", tags=["api-keys"])

ProviderType = Literal["anthropic", "openai", "openrouter"]


# Request/Response Models
class TestKeyRequest(BaseModel):
    provider: ProviderType
    api_key: str


class TestKeyResponse(BaseModel):
    valid: bool
    error: str | None = None


class SetKeyRequest(BaseModel):
    api_key: str


class SetKeyResponse(BaseModel):
    success: bool
    provider: str


class DeleteKeyResponse(BaseModel):
    success: bool
    provider: str


class ApiKeyStatus(BaseModel):
    provider: str
    status: Literal["personal", "global", "none"]
    masked_key: str | None = None


class StatusResponse(BaseModel):
    keys: list[ApiKeyStatus]


# Endpoints
@router.post("/test", response_model=TestKeyResponse)
async def test_api_key(
    request: TestKeyRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Test if an API key is valid without saving it.
    
    Makes a minimal API call to verify the key works.
    """
    is_valid, error = await api_key_service.test_api_key(
        request.provider, 
        request.api_key
    )
    
    return TestKeyResponse(valid=is_valid, error=error)


@router.get("/status", response_model=StatusResponse)
async def get_key_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status of API keys for all providers.
    
    Shows whether each provider uses:
    - "personal": User's own encrypted key
    - "global": Global .env fallback key
    - "none": No key available
    """
    status_dict = await api_key_service.get_api_key_status(db, str(current_user.id))
    
    # Get masked keys for display
    keys = []
    for provider in ["anthropic", "openai", "openrouter"]:
        status = status_dict[provider]
        
        # Get masked key if available
        masked = None
        if status == "personal":
            # Get user's key and mask it
            api_key = await api_key_service.get_api_key(db, str(current_user.id), provider)
            if api_key:
                masked = mask_api_key(api_key)
        elif status == "global":
            masked = "Using global key"
        
        keys.append(ApiKeyStatus(
            provider=provider,
            status=status,
            masked_key=masked
        ))
    
    return StatusResponse(keys=keys)


@router.put("/{provider}", response_model=SetKeyResponse)
async def set_api_key(
    provider: ProviderType,
    request: SetKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save an encrypted API key for the current user.
    
    The key is encrypted before storage using Fernet encryption.
    """
    success = await api_key_service.set_api_key(
        db,
        str(current_user.id),
        provider,
        request.api_key
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save API key")
    
    return SetKeyResponse(success=True, provider=provider)


@router.delete("/{provider}", response_model=DeleteKeyResponse)
async def delete_api_key(
    provider: ProviderType,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete the user's API key for a provider.
    
    After deletion, the system will fallback to the global .env key if available.
    """
    success = await api_key_service.delete_api_key(
        db,
        str(current_user.id),
        provider
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete API key")
    
    return DeleteKeyResponse(success=True, provider=provider)
