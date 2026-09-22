"""Dependencies module: FastAPI ``Depends`` factories.

Centralised here so routers stay declarative. ``get_db`` is the
async session lifecycle, ``get_current_user`` reads the JWT from the
session cookie (Phase 1 chose HttpOnly + CSRF over Authorization
header because the dashboard already mounts Vue's <a> / fetch from
JS where XSS is the bigger threat model).
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db import session_scope
from app.models.user import User

# HTTPBearer is the documented FastAPI helper for bearer-token auth.
# We register it here so routers can declare ``Depends(get_current_user)``
# without each router re-instantiating the security scheme.
_bearer = HTTPBearer(auto_error=False)


def settings_dep() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(settings_dep)]


async def get_db() -> AsyncSession:
    async for session in session_scope():
        yield session


DbDep = Annotated[AsyncSession, Depends(get_db)]


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _decode_jwt(token: str, settings: Settings) -> dict[str, Any]:
    """Verify a JWT and return its claims. Raises 401 on failure."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    db: DbDep,
    settings: SettingsDep,
) -> User:
    """Resolve the current user from the session cookie (preferred)
    or the Authorization: Bearer header (fallback for API clients).
    """
    token: str | None = None
    bearer = request.cookies.get("cenidim_session")
    if bearer:
        token = bearer
    elif request.headers.get("authorization", "").lower().startswith("bearer "):
        token = request.headers["authorization"].split(" ", 1)[1]
    else:
        auth = await _bearer(request)
        if isinstance(auth, HTTPAuthorizationCredentials):
            token = auth.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = _decode_jwt(token, settings)
    sub = claims.get("sub")
    # python-jose enforces ``sub`` to be a string at mint time; we
    # accept either and coerce to int for the user lookup.
    try:
        user_id = int(sub) if sub is not None else None
    except (TypeError, ValueError):
        user_id = None
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(min_role: str):
    """Build a dependency that asserts the current user has at least the
    given role. Roles are ordered: viewer < editor < admin.
    """
    levels = {"viewer": 1, "editor": 2, "admin": 3}

    async def _check(user: CurrentUser) -> User:
        user_level = levels.get(user.role, 0)
        required = levels.get(min_role, 99)
        if user_level < required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{min_role}' required (you are '{user.role}')",
            )
        return user

    return _check


def issue_access_token(user: User, settings: Settings) -> tuple[str, datetime]:
    """Mint a fresh access token. Returns (token, expires_at).

    Note: python-jose requires the ``sub`` claim to be a string at
    mint time (it enforces the spec). We coerce the int user id via
    ``str()`` here; the consumer (``get_current_user``) coerces back.
    """
    now = _now_utc()
    exp = now + timedelta(seconds=settings.jwt_access_ttl_seconds)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    return token, exp


__all__ = [
    "SettingsDep",
    "DbDep",
    "CurrentUser",
    "get_db",
    "get_current_user",
    "require_role",
    "issue_access_token",
]
