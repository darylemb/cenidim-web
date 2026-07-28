"""Auth service: register / login / restore / password reset.

Each mutating function is intentionally narrow so the FastAPI
router layer just forwards results. All side effects (audit log,
email outbox, refresh-token revocation) happen here.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.security import (
    hash_password,
    issue_jwt,
    verify_legacy_password,
    verify_password,
    verify_password_policy,
)


class AuthError(Exception):
    """Domain auth error. Routers translate this to an HTTP response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


async def register_user(
    db: AsyncSession,
    *,
    username: str,
    email: str,
    password: str,
    settings: Settings,
) -> User:
    """Create a viewer-tier user with the canonical bootstrap email.

    Raises AuthError(409) on username / email collision.
    """
    err = verify_password_policy(password)
    if err is not None:
        raise AuthError(400, err)
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="viewer",
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        raise AuthError(409, "Username or email already exists")
    return user


async def authenticate(
    db: AsyncSession, *, username: str, password: str
) -> User:
    user = (
        await db.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()
    if user is None:
        raise AuthError(401, "Invalid credentials")

    if verify_password(password, user.password_hash):
        return user

    # Legacy fallback: the Go backend used ``bcrypt(plain)`` while
    # the FastAPI service uses ``bcrypt(sha256(plain))``. Until
    # every Go-created user is rehashed, accept the legacy hash so
    # the cutover doesn't lock out the admin. On a legacy match we
    # opportunistically rehash so the next login uses the fast path.
    if verify_legacy_password(password, user.password_hash):
        user.password_hash = hash_password(password)
        await db.flush()
        return user

    raise AuthError(401, "Invalid credentials")


def issue_session(user: User, settings: Settings) -> dict[str, tuple[str, datetime]]:
    """Mint the access + refresh tokens + the CSRF seed."""
    access, access_exp = issue_jwt(
        subject=user.id,
        role=user.role,
        ttl_seconds=settings.jwt_access_ttl_seconds,
        secret=settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        token_type="access",  # noqa: S106
    )
    refresh, refresh_exp = issue_jwt(
        subject=user.id,
        role=user.role,
        ttl_seconds=settings.jwt_refresh_ttl_seconds,
        secret=settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        token_type="refresh",  # noqa: S106
    )
    return {
        "access": (access, access_exp),
        "refresh": (refresh, refresh_exp),
    }


async def request_password_reset(
    db: AsyncSession, *, email: str, settings: Settings
) -> tuple[str | None, str | None]:
    """Always returns (dev_link_or_none, error_or_none).

    The caller is expected to translate that into a 200 response
    regardless of whether the email exists (avoid user enumeration).
    The plaintext reset link is included in the return tuple ONLY
    when ``settings.email_demo_print_body`` is True.
    """
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is None:
        return None, None
    from app.services.email import EmailService  # local import avoids cycle

    token, token_hash = _make_reset_token_pair()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(UTC)
            + timedelta(seconds=settings.jwt_access_ttl_seconds),  # 1h same as access
        )
    )
    reset_url = f"{settings.frontend_base_url}/reset?token={token}"
    await db.flush()
    await EmailService.enqueue(
        to=user.email,
        subject="CENIDIM — Recupera tu contraseña",
        body=EmailService.build_reset_body(user.username, reset_url),
        kind="password_reset",
        related_user_id=user.id,
        db=db,
    )
    if settings.email_demo_print_body:
        return reset_url, None
    return None, None


def _make_reset_token_pair() -> tuple[str, str]:
    """Wrap the helper so callers don't import the security module."""
    from app.security import generate_reset_token
    return generate_reset_token()


async def consume_password_reset(
    db: AsyncSession, *, token: str, new_password: str
) -> None:
    """Validate token, rotate hash, mark used, invalidate siblings.

    Raises AuthError(401) for any validation failure.
    """
    from datetime import datetime

    from sqlalchemy import update

    from app.security import hash_password

    err = verify_password_policy(new_password)
    if err is not None:
        raise AuthError(400, err)

    now = datetime.now(UTC)
    rows = (
        await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
        )
    ).scalars().all()
    matched: PasswordResetToken | None = None
    for row in rows:
        # bcrypt verification; constant-time per row.
        if _verify_bcrypt_safe(token, row.token_hash):
            matched = row
            break
    if matched is None:
        raise AuthError(401, "Token inválido o expirado")
    # Rotate the password hash.
    user = (
        await db.execute(select(User).where(User.id == matched.user_id))
    ).scalar_one_or_none()
    if user is None:
        raise AuthError(401, "Token inválido o expirado")
    user.password_hash = hash_password(new_password)
    user.last_sign_in_method = "password"
    user.last_sign_in_at = now
    # Mark this token used AND invalidate any other unredeemed
    # tokens for the same user so a stolen link can't be replayed.
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    await db.flush()


def _verify_bcrypt_safe(token: str, hashed: str) -> bool:
    """bcrypt-verify ``token`` against ``hashed``.

    The token was originally pre-hashed with SHA-256 before bcrypt on
    the creation path (see ``app.security._prep``); we replicate that
    here so direct ``bcrypt.checkpw`` matches.
    """
    try:
        import bcrypt

        from app.security import _prep

        return bcrypt.checkpw(_prep(token), hashed.encode("ascii"))
    except Exception:
        return False


__all__ = [
    "AuthError",
    "authenticate",
    "consume_password_reset",
    "issue_session",
    "register_user",
    "request_password_reset",
]
