"""
Encryption utilities for sensitive data like API keys.

Uses Fernet (symmetric encryption) with a key derived from the app SECRET_KEY.
"""

import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

logger = logging.getLogger(__name__)


def _get_encryption_key() -> bytes:
    """
    Generate a deterministic encryption key from the app's SECRET_KEY.
    
    Uses SHA256 to hash the secret key and then base64-encodes it to create
    a valid Fernet key (32 url-safe base64-encoded bytes).
    
    Returns:
        bytes: A valid Fernet encryption key
    """
    # Hash the secret key to get consistent 32 bytes
    key_hash = hashlib.sha256(settings.secret_key.encode()).digest()
    # Fernet requires base64-encoded key
    return base64.urlsafe_b64encode(key_hash)


def encrypt_api_key(plain_key: str) -> Optional[str]:
    """
    Encrypt an API key for secure storage.
    
    Args:
        plain_key: The plain text API key to encrypt
        
    Returns:
        The encrypted key as a base64-encoded string, or None if encryption fails
        
    Example:
        >>> encrypted = encrypt_api_key("sk-ant-api03_abc123")
        >>> encrypted
        'gAAAAABl...'  # Fernet encrypted token
    """
    if not plain_key:
        return None
        
    try:
        fernet = Fernet(_get_encryption_key())
        encrypted_bytes = fernet.encrypt(plain_key.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to encrypt API key: {e}")
        return None


def decrypt_api_key(encrypted_key: str) -> Optional[str]:
    """
    Decrypt an encrypted API key.
    
    Args:
        encrypted_key: The encrypted key (base64-encoded Fernet token)
        
    Returns:
        The decrypted plain text API key, or None if decryption fails
        
    Example:
        >>> decrypted = decrypt_api_key('gAAAAABl...')
        >>> decrypted
        'sk-ant-api03_abc123'
    """
    if not encrypted_key:
        return None
        
    try:
        fernet = Fernet(_get_encryption_key())
        decrypted_bytes = fernet.decrypt(encrypted_key.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except InvalidToken:
        logger.error("Failed to decrypt API key: Invalid token (wrong key or corrupted data)")
        return None
    except Exception as e:
        logger.error(f"Failed to decrypt API key: {e}")
        return None


def mask_api_key(api_key: Optional[str]) -> str:
    """
    Mask an API key for display purposes (show only first 7 and last 4 characters).
    
    Args:
        api_key: The API key to mask
        
    Returns:
        Masked key string
        
    Example:
        >>> mask_api_key("sk-ant-api03_abc123xyz789")
        'sk-ant-...z789'
        >>> mask_api_key(None)
        'Not set'
    """
    if not api_key:
        return "Not set"
    
    if len(api_key) < 12:
        return "****"
    
    return f"{api_key[:7]}...{api_key[-4:]}"
