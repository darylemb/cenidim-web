"""Google OAuth: /api/auth/google/start + /callback.

Mirrors the Go ``handlers/oauth_google.go`` surface. The id-token
verifier is abstracted behind a tiny protocol so tests can swap a
``StubIDTokenVerifier`` in without needing the real google ID-token
SDK or network access. Production wiring happens in
``app.services.google_oauth.GoogleOAuthClient``.

Phase 1a (current): the route is fully wired but Google OAuth is
intentionally NOT shown on the dashboard login page (see
``frontend/src/views/LoginView.vue``). Phase 7 brings it back as an
admin-only link.
"""
from __future__ import annotations

import base64
import logging
import os
import secrets
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, Response
from sqlalchemy import select

from app import db as db_module
from app.config import Settings, get_settings
from app.models.user import User
from app.models.user_identity import UserIdentity
from app.security import hash_password, issue_jwt

router = APIRouter(prefix="/api/auth/google", tags=["auth", "google"])
_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verifier protocol (testability)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class GoogleIDTokenClaims:
    """Subset of claims we care about for sign-in."""

    sub: str
    email: str
    email_verified: bool
    aud: str = ""
    name: str | None = None
    picture: str | None = None


class IDTokenVerifier(Protocol):
    """Test-friendly seam. Production wires a google-jwt verifier
    in via ``app.services.google_oauth.GoogleIDTokenValidator``.
    """

    async def verify(self, raw_token: str) -> GoogleIDTokenClaims:  # pragma: no cover - protocol
        ...


class StubIDTokenVerifier:
    """In-memory verifier used by tests. Returns the canned claims
    set in the constructor; raises ValueError on bad tokens.
    """

    def __init__(self, claims: GoogleIDTokenClaims | None = None, error: Exception | None = None) -> None:
        self._claims = claims
        self._error = error
        self.seen_tokens: list[str] = []

    async def verify(self, raw_token: str) -> GoogleIDTokenClaims:
        self.seen_tokens.append(raw_token)
        if self._error is not None:
            raise self._error
        if self._claims is None:
            raise ValueError("no canned claims configured")
        return self._claims


# Module-level registry so tests can swap verifiers in without touching
# the env-based wiring.
_active_verifier: IDTokenVerifier | None = None
_active_admin_emails: set[str] = set()


def configure_verifier(
    verifier: IDTokenVerifier | None = None,
    *,
    admin_emails: set[str] | None = None,
) -> None:
    """Replace the active id-token verifier (used by tests + by
    ``app.services.google_oauth.configure`` at startup).
    """
    global _active_verifier, _active_admin_emails
    if verifier is not None:
        _active_verifier = verifier
    if admin_emails is not None:
        _active_admin_emails = {e.strip().lower() for e in admin_emails if e.strip()}


def _load_admin_emails_from_env() -> set[str]:
    raw = os.environ.get("ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _get_verifier() -> IDTokenVerifier:
    """Lazy-init the production verifier once at first request."""
    global _active_verifier
    if _active_verifier is not None:
        return _active_verifier
    try:
        from app.services.google_oauth import build_default_verifier
        _active_verifier = build_default_verifier()
    except Exception as exc:  # noqa: BLE001
        _log.warning("Google OAuth verifier could not be initialised: %s", exc)
        raise
    return _active_verifier


# ---------------------------------------------------------------------------
# State cookie helpers
# ---------------------------------------------------------------------------


def _random_state() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(24)).rstrip(b"=").decode("ascii")


def _secure_from_request(request: Request, settings: Settings) -> bool:
    if request.headers.get("x-forwarded-proto", "").lower() == "https":
        return True
    return request.url.scheme == "https" or settings.is_prod


@router.get("/start")
async def google_auth_start(
    request: Request, response: Response, settings: Settings = None
) -> Response:
    """Redirect to Google's consent screen with a state cookie."""
    settings = settings or get_settings()
    try:
        verifier_or_client = _get_verifier()
        del verifier_or_client  # not used directly here
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Google sign-in is not configured: {exc}")

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URL", "")
    if not client_id or not redirect_uri:
        raise HTTPException(status_code=500, detail="Google sign-in is not configured")

    state = _random_state()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    location = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    secure = _secure_from_request(request, settings)
    response = Response(status_code=302)
    response.headers["Location"] = location
    response.set_cookie(
        "oauth_state",
        state,
        path="/api/auth/google",
        max_age=600,
        httponly=True,
        secure=secure,
        samesite="lax",
    )
    return response


@router.get("/callback")
async def google_auth_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    settings: Settings = None,
) -> Response:
    """Validate state, exchange code for tokens, sign the user in."""
    settings = settings or get_settings()
    frontend_url = os.environ.get("FRONTEND_BASE_URL", settings.frontend_base_url)

    state_cookie = request.cookies.get("oauth_state")
    if not state_cookie or not state or state_cookie != state:
        return _redirect_with_error(frontend_url, "state_mismatch")

    if error:
        return _redirect_with_error(frontend_url, "user_cancelled")

    if not code:
        return _redirect_with_error(frontend_url, "missing_code")

    verifier = _get_verifier()
    try:
        claims = await verifier.verify(code)
    except Exception as exc:
        _log.info("Google id_token verification failed: %s", exc)
        return _redirect_with_error(frontend_url, "upstream")

    if not claims.email_verified:
        return _redirect_with_error(frontend_url, "email_not_verified")

    user, auto_provisioned = await _find_or_create_user(claims, settings)
    await _link_identity(user.id, claims)
    access, _ = issue_jwt(
        subject=user.id,
        role=user.role,
        ttl_seconds=settings.jwt_access_ttl_seconds,
        secret=settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        token_type="access",  # noqa: S106
    )

    # Cookies
    response = Response(
        status_code=302,
        headers={
            "Location": (
                f"{frontend_url}/login?google=ok&google_auto={'1' if auto_provisioned else '0'}"
                f"#token={access}&id={user.id}&username={user.username}"
                f"&email={user.email}&role={user.role}"
            )
        },
    )
    response.delete_cookie("oauth_state", path="/api/auth/google")
    response.set_cookie(
        "cenidim_session",
        access,
        max_age=settings.jwt_access_ttl_seconds,
        httponly=True,
        secure=settings.is_prod,
        samesite="lax",
        path="/",
    )
    return response


def _redirect_with_error(frontend_url: str, code: str) -> Response:
    """302 to the frontend with ?google=err=<code>."""
    sep = "&" if "?" in frontend_url else "?"
    return Response(
        status_code=302,
        headers={"Location": f"{frontend_url}{sep}google=err={code}"},
    )


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def _find_or_create_user(
    claims: GoogleIDTokenClaims, settings: Settings
) -> tuple[User, bool]:
    """SELECT by email, INSERT with a unique username if missing.

    Returns ``(user, auto_provisioned)``. The role defaults to
    ``viewer`` unless the email is in ``ADMIN_EMAILS``.
    """
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        row = (
            await session.execute(select(User).where(User.email == claims.email))
        ).scalar_one_or_none()
        if row is not None:
            row.last_sign_in_method = "google"
            from datetime import UTC, datetime

            row.last_sign_in_at = datetime.now(UTC)
            await session.commit()
            return row, False

        username = claims.email.split("@", 1)[0]
        unique = username
        for _ in range(50):
            existing = (
                await session.execute(
                    select(User).where(User.username == unique)
                )
            ).scalar_one_or_none()
            if existing is None:
                break
            unique = f"{username}{secrets.randbelow(10000)}"
        else:
            unique = f"{username}{secrets.token_hex(4)}"

        admin_set = _active_admin_emails or _load_admin_emails_from_env()
        is_admin_email = claims.email.lower() in admin_set
        user = User(
            username=unique,
            email=claims.email,
            # Sentinel marker so we can distinguish google-only accounts
            # in the DB; the real password is never set in this flow.
            password_hash=hash_password(secrets.token_urlsafe(32)) or "GOOGLE_LINKED",
            role="admin" if is_admin_email else "viewer",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, True


async def _link_identity(user_id: int, claims: GoogleIDTokenClaims) -> None:
    """Upsert the user_identities row for this provider."""
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        existing = (
            await session.execute(
                select(UserIdentity).where(
                    UserIdentity.user_id == user_id,
                    UserIdentity.provider == "google",  # noqa: S106
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.subject = claims.sub
            existing.email_at_link = claims.email
        else:
            session.add(
                UserIdentity(
                    user_id=user_id,
                    provider="google",
                    subject=claims.sub,
                    email_at_link=claims.email,
                )
            )
        await session.commit()


__all__ = [
    "GoogleIDTokenClaims",
    "IDTokenVerifier",
    "StubIDTokenVerifier",
    "configure_verifier",
    "router",
]
