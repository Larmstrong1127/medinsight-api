import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_scheme)) -> str:
    settings = get_settings()
    if not api_key or api_key not in settings.get_api_keys():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


def _get_fernet() -> Fernet:
    settings = get_settings()
    key = settings.encryption_key
    if not key:
        # Generate a deterministic dev key when none is configured — never use in production
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_content(plaintext: str) -> str:
    """Encrypt document content for storage. Returns base64-encoded ciphertext."""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_content(ciphertext: str) -> str:
    """Decrypt stored document content."""
    try:
        fernet = _get_fernet()
        return fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken as err:
        raise ValueError("Content decryption failed — key mismatch or tampered data") from err
