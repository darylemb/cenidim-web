"""Tests for the admin identity (Google OAuth) management UI."""
from __future__ import annotations

import pytest

from tests.conftest import login_as, make_admin, make_identity, make_user


@pytest.mark.asyncio
async def test_admin_users_tab_lists_identities(db_session, app_client):
    """The admin users table renders the linked identities column."""
    await make_admin()
    await make_identity(user_id=1, subject="google-test-subject-1")
    await login_as(app_client, "admin", "admin1234")

    # The identities endpoint is fetched from /api/admin/users/{id}/identities.
    r = await app_client.get("/api/admin/users/1/identities")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["provider"] == "google"
    assert rows[0]["subject"] == "google-test-subject-1"


@pytest.mark.asyncio
async def test_admin_users_tab_handles_user_with_no_identities(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    r = await app_client.get("/api/admin/users/1/identities")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_admin_can_unlink_identity(db_session, app_client):
    await make_admin()
    await make_identity(user_id=1, subject="to-unlink")
    await login_as(app_client, "admin", "admin1234")

    # Confirm it exists.
    r = await app_client.get("/api/admin/users/1/identities")
    assert len(r.json()) == 1

    # Unlink.
    r = await app_client.delete("/api/admin/users/1/identity")
    assert r.status_code == 204

    # Confirm gone.
    r = await app_client.get("/api/admin/users/1/identities")
    assert r.json() == []


@pytest.mark.asyncio
async def test_unlink_unknown_identity_returns_404(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    r = await app_client.delete("/api/admin/users/1/identity")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_unlink_requires_admin_role(db_session, app_client):
    """Editor + viewer cannot manage Google identities."""
    await make_admin()
    await make_user(
        username="editor",
        email="editor@cenidim.example",
        password="Strong1234",
        role="editor",
    )
    await make_identity(user_id=1, subject="protected-google-sub")
    await login_as(app_client, "editor", "Strong1234")
    r = await app_client.delete("/api/admin/users/1/identity")
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_unlink_invalid_id_returns_422(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    r = await app_client.delete("/api/admin/users/notanint/identity")
    assert r.status_code == 422
