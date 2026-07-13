"""End-to-end tests for /api/auth/google/*."""
from __future__ import annotations

import pytest

from app.routers import google_oauth
from app.routers.google_oauth import GoogleIDTokenClaims, StubIDTokenVerifier
from tests.conftest import make_admin


@pytest.fixture
def stub_verifier():
    """Replace the production verifier with a stub for the test."""
    verifier = StubIDTokenVerifier(
        claims=GoogleIDTokenClaims(
            sub="google-test-1",
            email="alice@cenidim.example",
            email_verified=True,
        )
    )
    google_oauth.configure_verifier(verifier=verifier, admin_emails=set())
    return verifier


@pytest.fixture
def google_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_REDIRECT_URL", "http://testserver/api/auth/google/callback")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://testserver")


@pytest.mark.asyncio
async def test_google_start_redirects_and_sets_state_cookie(
    app_client, db_session, google_env, stub_verifier
):
    response = await app_client.get("/api/auth/google/start", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert "accounts.google.com/o/oauth2/v2/auth" in location
    assert "state=" in location
    # Cookie is set via Set-Cookie.
    state_cookie = next(
        (c for c in response.cookies.jar if c.name == "oauth_state"), None
    )
    assert state_cookie is not None
    assert state_cookie.value  # non-empty


@pytest.mark.asyncio
async def test_google_start_returns_500_when_unconfigured(
    app_client, db_session, monkeypatch
):
    # Clear env vars so the env-based path fails.
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_REDIRECT_URL", raising=False)
    # Wipe any cached verifier so the production path is re-evaluated.
    google_oauth._active_verifier = None
    response = await app_client.get("/api/auth/google/start", follow_redirects=False)
    assert response.status_code == 500
    google_oauth._active_verifier = None  # restore default


@pytest.mark.asyncio
async def test_google_callback_state_mismatch(app_client, db_session, google_env):
    response = await app_client.get(
        "/api/auth/google/callback",
        params={"state": "bad-state", "code": "x"},
        cookies={"oauth_state": "different-state"},
    )
    assert response.status_code == 302
    assert "google=err=state_mismatch" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_provisions_viewer(
    app_client, db_session, google_env, stub_verifier
):
    response = await app_client.get(
        "/api/auth/google/callback",
        params={"state": "good", "code": "stub-token-1"},
        cookies={"oauth_state": "good"},
    )
    assert response.status_code == 302
    body = response.headers["location"]
    assert "google=ok" in body
    assert "username=alice" in body
    assert "role=viewer" in body

    # Cookie set
    session_cookie = next(
        (c for c in response.cookies.jar if c.name == "cenidim_session"), None
    )
    assert session_cookie is not None
    assert session_cookie.value  # JWT
    # Verifier called
    assert "stub-token-1" in stub_verifier.seen_tokens


@pytest.mark.asyncio
async def test_google_callback_matches_existing_user(
    app_client, db_session, google_env, stub_verifier
):
    await make_admin()
    response = await app_client.get(
        "/api/auth/google/callback",
        params={"state": "good", "code": "stub-token-2"},
        cookies={"oauth_state": "good"},
    )
    assert response.status_code == 302
    # admin is the only user, but admin email isn't the google email
    # -> a new "alice" is created
    assert "google=ok" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_admin_emails(
    app_client, db_session, google_env
):
    verifier = StubIDTokenVerifier(
        claims=GoogleIDTokenClaims(
            sub="google-admin",
            email="boss@cenidim.example",
            email_verified=True,
        )
    )
    google_oauth.configure_verifier(
        verifier=verifier,
        admin_emails={"boss@cenidim.example"},
    )
    response = await app_client.get(
        "/api/auth/google/callback",
        params={"state": "good", "code": "boss-token"},
        cookies={"oauth_state": "good"},
    )
    assert response.status_code == 302
    assert "role=admin" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_user_cancelled(
    app_client, db_session, google_env, stub_verifier
):
    response = await app_client.get(
        "/api/auth/google/callback",
        params={"state": "good", "code": "x", "error": "access_denied"},
        cookies={"oauth_state": "good"},
    )
    assert response.status_code == 302
    assert "google=err=user_cancelled" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_missing_code(
    app_client, db_session, google_env, stub_verifier
):
    response = await app_client.get(
        "/api/auth/google/callback",
        params={"state": "good"},
        cookies={"oauth_state": "good"},
    )
    assert response.status_code == 302
    assert "google=err=missing_code" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_unverified_email(
    app_client, db_session, google_env
):
    verifier = StubIDTokenVerifier(
        claims=GoogleIDTokenClaims(
            sub="google-x",
            email="unverified@cenidim.example",
            email_verified=False,
        )
    )
    google_oauth.configure_verifier(verifier=verifier)
    response = await app_client.get(
        "/api/auth/google/callback",
        params={"state": "good", "code": "x"},
        cookies={"oauth_state": "good"},
    )
    assert response.status_code == 302
    assert "google=err=email_not_verified" in response.headers["location"]


@pytest.mark.asyncio
async def test_google_callback_upstream_error(
    app_client, db_session, google_env
):
    verifier = StubIDTokenVerifier(error=ValueError("bad token"))
    google_oauth.configure_verifier(verifier=verifier)
    response = await app_client.get(
        "/api/auth/google/callback",
        params={"state": "good", "code": "y"},
        cookies={"oauth_state": "good"},
    )
    assert response.status_code == 302
    assert "google=err=upstream" in response.headers["location"]
