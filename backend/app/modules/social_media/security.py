"""Encryption helpers for provider credentials and one-time OAuth state."""

import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException


def _fernet() -> Fernet:
    key = get_settings().social_token_encryption_key
    if not key:
        raise ExternalServiceException(message="Social token encryption key is not configured")
    try:
        return Fernet(key.encode())
    except (TypeError, ValueError) as exc:
        raise ExternalServiceException(message="Social token encryption key is invalid") from exc


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise ExternalServiceException(message="Stored social credential cannot be decrypted") from exc


def hash_state(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
