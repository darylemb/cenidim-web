"""Security helpers: password hashing + JWT + CSRF double-submit."""
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import jwt

# bcrypt's hard 72-byte input limit is bypassed by pre-hashing with
# SHA-256 first. The hex digest is 64 ASCII bytes (well within the
# limit), and the bcrypt layer still provides per-password salts and
# the slow factor. This is the same pattern Django and others use.


def _prep(plain: str) -> bytes:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_prep(plain), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prep(plain), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


def verify_legacy_password(plain: str, hashed: str) -> bool:
    """Verify a password against a legacy raw-bcrypt hash.

    The Go backend (``backend/cmd/build-db`` /
    ``backend/handlers/auth.go``) used
    ``bcrypt.GenerateFromPassword(plain)`` directly. The FastAPI
    service uses ``bcrypt(sha256(plain))`` so the two formats are
    not interchangeable. Until every Go-created user has been
    migrated, ``authenticate`` falls back to this helper; on a match
    the caller is expected to re-hash the password with the new
    scheme so the next login uses the fast path.

    Returns ``False`` (and never raises) on malformed hashes.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


def generate_reset_token() -> tuple[str, str]:
    """Return (plaintext_token, hashed_for_db).

    The plaintext is URL-safe base64 (~43 chars). The hash is bcrypt
    so a DB leak does not yield usable reset links.
    """
    raw = secrets.token_urlsafe(32)
    hashed = bcrypt.hashpw(_prep(raw), bcrypt.gensalt(rounds=12)).decode("ascii")
    return raw, hashed


def hash_reset_token(plaintext: str) -> str:
    """Bcrypt an existing plaintext (used when verifying)."""
    return bcrypt.hashpw(_prep(plaintext), bcrypt.gensalt(rounds=12)).decode("ascii")


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
    now = datetime.now(UTC)
    exp = now + timedelta(seconds=ttl_seconds)
    payload: dict[str, Any] = {
        "sub": str(subject),
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
    "verify_legacy_password",
    "generate_reset_token",
    "hash_reset_token",
    "issue_jwt",
    "issue_csrf_token",
    "verify_password_policy",
]
