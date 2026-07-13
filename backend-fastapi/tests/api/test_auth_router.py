"""End-to-end tests for /api/auth/* (login / register / forgot / reset /
refresh / logout).
"""
from __future__ import annotations

import pytest

from tests.conftest import login_as, make_admin


def _override_demo_email(settings):
    """Flip ``email_demo_print_body=True`` on the cached Settings
    singleton (which the FastAPI app reads via ``get_settings()``)
    AND on the test's local copy so the running router sees the
    change.
    """
    from app.config import get_settings as _gs

    settings.email_demo_print_body = True
    cached = _gs()
    cached.email_demo_print_body = True
    from app.services.email import EmailService

    EmailService.configure(cached)


@pytest.mark.asyncio
async def test_login_with_invalid_credentials(app_client, db_session):
    await make_admin()
    response = await app_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_unknown_user(app_client, db_session):
    response = await app_client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "anything1"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_succeeds_and_sets_cookies(app_client, db_session):
    await make_admin()
    response = await app_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin1234"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["username"] == "admin"
    cookie_names = {c.name for c in response.cookies.jar}
    assert "cenidim_session" in cookie_names


@pytest.mark.asyncio
async def test_login_validation_error(app_client, db_session):
    response = await app_client.post(
        "/api/auth/login",
        json={"username": "", "password": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_then_login(app_client, db_session):
    response = await app_client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@cenidim.example",
            "password": "Strong1234",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["user"]["username"] == "newuser"


@pytest.mark.asyncio
async def test_register_rejects_weak_password(app_client, db_session):
    response = await app_client.post(
        "/api/auth/register",
        json={
            "username": "weakuser",
            "email": "w@cenidim.example",
            "password": "nodigits",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_rejects_duplicate_username(app_client, db_session):
    await make_admin()
    response = await app_client.post(
        "/api/auth/register",
        json={
            "username": "admin",
            "email": "newadmin@cenidim.example",
            "password": "Strong1234",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_forgot_password_returns_ok_and_dev_link(
    app_client, db_session, settings
):
    _override_demo_email(settings)
    await make_admin()
    response = await app_client.post(
        "/api/auth/forgot",
        json={"email": "admin@cenidim.example"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    # dev_link is non-empty because email_demo_print_body=True
    assert body["dev_link"]


@pytest.mark.asyncio
async def test_forgot_password_unknown_email_silent(app_client, db_session):
    response = await app_client.post(
        "/api/auth/forgot",
        json={"email": "ghost@cenidim.example"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reset_password_roundtrip(
    app_client, db_session, settings
):
    _override_demo_email(settings)
    await make_admin()
    forgot = await app_client.post(
        "/api/auth/forgot",
        json={"email": "admin@cenidim.example"},
    )
    dev_link = forgot.json()["dev_link"]
    token = dev_link.split("token=")[1]

    reset = await app_client.post(
        "/api/auth/reset",
        json={"token": token, "new_password": "NewSecret123"},
    )
    assert reset.status_code == 200

    login = await app_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "NewSecret123"},
    )
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_reset_rejects_bad_token(app_client, db_session):
    response = await app_client.post(
        "/api/auth/reset",
        json={"token": "nope", "new_password": "NewSecret123"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_reset_rejects_weak_password(
    app_client, db_session, settings
):
    _override_demo_email(settings)
    await make_admin()
    forgot = await app_client.post(
        "/api/auth/forgot",
        json={"email": "admin@cenidim.example"},
    )
    dev_link = forgot.json()["dev_link"]
    token = dev_link.split("token=")[1]
    response = await app_client.post(
        "/api/auth/reset",
        json={"token": token, "new_password": "nodigits"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_refresh_rotates_jti(app_client, db_session):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    refresh_cookie = next(
        (c for c in app_client.cookies.jar if c.name == "cenidim_refresh"), None
    )
    assert refresh_cookie is not None
    token1 = refresh_cookie.value

    # First refresh should succeed and rotate the jti
    response = await app_client.post("/api/auth/refresh")
    assert response.status_code == 200
    # Pull the refresh cookie off the response itself (httpx may or
    # may not propagate into the jar depending on path matching).
    new_token = None
    for raw in response.headers.raw:
        if raw[0].lower() != b"set-cookie":
            continue
        cs = raw[1].decode() if isinstance(raw[1], bytes) else raw[1]
        head = cs.split(";", 1)[0]
        if head.startswith("cenidim_refresh="):
            new_token = head.split("=", 1)[1]
    assert new_token is not None
    assert new_token != token1, "refresh must rotate the jti"

    # Use the OLD refresh token — should be 401 because it's revoked.
    app_client.cookies.set(
        "cenidim_refresh", token1, path="/api/auth/refresh"
    )
    response = await app_client.post("/api/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_without_cookie_returns_401(app_client, db_session):
    await make_admin()
    response = await app_client.post("/api/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_bogus_token_returns_401(app_client, db_session):
    await make_admin()
    app_client.cookies.set(
        "cenidim_refresh", "not-a-real-jwt", path="/api/auth/refresh"
    )
    response = await app_client.post("/api/auth/refresh")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_clears_session(app_client, db_session):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.post("/api/auth/logout")
    assert response.status_code == 200
    # The response must include a Set-Cookie that expires cenidim_session.
    cleared_session = False
    cleared_refresh = False
    for raw in response.headers.raw:
        if raw[0].lower() != b"set-cookie":
            continue
        cs = raw[1].decode() if isinstance(raw[1], bytes) else raw[1]
        if "cenidim_session=" in cs and ("max-age=0" in cs.lower() or "expires=" in cs.lower()):
            cleared_session = True
        if "cenidim_refresh=" in cs and ("max-age=0" in cs.lower() or "expires=" in cs.lower()):
            cleared_refresh = True
    assert cleared_session
    assert cleared_refresh


@pytest.mark.asyncio
async def test_logout_without_session_still_succeeds(app_client, db_session):
    await make_admin()
    response = await app_client.post("/api/auth/logout")
    assert response.status_code == 200
