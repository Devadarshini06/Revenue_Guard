"""
RevenueGuard JWT & Token Lifecycle Utilities
============================================
Handles short-lived JWT access tokens, cryptographic refresh tokens,
and token validation/hashing.
"""

import jwt
import uuid
import secrets
import hashlib
import time
from datetime import datetime, timedelta, timezone, timezone
from typing import Dict, Any, Optional
from backend.config import settings

# JWT Configuration
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(
    user_id: int,
    email: str,
    role: str,
    token_version: int = 1,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Creates a short-lived signed JWT access token using epoch timestamps."""
    now_ts = int(time.time())
    if expires_delta:
        exp_ts = now_ts + int(expires_delta.total_seconds())
    else:
        exp_ts = now_ts + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "tv": token_version,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now_ts,
        "exp": exp_ts
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises jwt.PyJWTError on expiration, tampering, or invalid claims.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[JWT_ALGORITHM]
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Token is not an access token.")

    return payload


def generate_refresh_token() -> str:
    """Generates a high-entropy cryptographically random refresh token."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    """Computes SHA-256 digest of refresh token for safe database persistence."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_refresh_token_expiration() -> datetime:
    """Returns expiration timestamp for a new refresh token."""
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
