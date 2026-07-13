"""Security helpers: password hashing + JWT + CSRF double-submit."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.config import Settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_ctx.verify(plain, hashed)
    except ValueError:
        return False


def generate_reset_token() -> tuple[str, str]:
    """Return (plaintext_token, hashed_for_db).

    The plaintext is URL-safe base64 (~43 chars). The hash is bcrypt
    so a DB leak does not yield usable reset links.
    """
    raw = secrets.token_urlsafe(32)
    hashed = _pwd_ctx.hash(raw)
    return raw, hashed


def hash_reset_token(plaintext: str) -> str:
    """Bcrypt an existing plaintext (used when verifying)."""
    return _pwd_ctx.hash(plaintext)


def issue_jwt(
    *,
    subject: int,
    role: str,
    ttl_seconds: int,
    secret: str,
    algorithm: str,
    token_type: str,
    extra: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    """Mint a signed JWT. Returns (token, expires_at)."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=ttl_seconds)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return token, exp


def issue_csrf_token() -> str:
    """Generate a CSRF token (one per session). Returned to the client
    in a non-HttpOnly cookie so JS can read it and echo it as the
    X-CSRF-Token header on every mutating request.
    """
    return secrets.token_urlsafe(32)


def verify_password_policy(plain: str) -> str | None:
    """Return an error message if the password violates the policy."""
    if len(plain) < 8:
        return "Password must be at least 8 characters"
    if len(plain) > 128:
        return "Password must be at most 128 characters"
    has_digit = any(c.isdigit() for c in plain)
    if not has_digit:
        return "Password must include at least one digit"
    return None


__all__ = [
    "hash_password",
    "verify_password",
    "generate_reset_token",
    "hash_reset_token",
    "issue_jwt",
    "issue_csrf_token",
    "verify_password_policy",
]
