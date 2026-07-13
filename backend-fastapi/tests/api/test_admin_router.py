"""End-to-end tests for the /api/admin/* router."""
from __future__ import annotations

import pytest

from tests.conftest import (
    login_as,
    make_admin,
    make_email_outbox,
    make_identity,
    make_user,
)


@pytest.mark.asyncio
async def test_admin_requires_auth(app_client):
    response = await app_client.get("/api/admin/fonogramas")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_forbidden_for_viewer(db_session, app_client):
    await make_admin()
    await make_user(
        username="bob", email="bob@cenidim.example", role="viewer"
    )
    await login_as(app_client, "bob", "Strong1234")
    response = await app_client.get("/api/admin/fonogramas")
    assert response.status_code == 200  # viewer can read

    response = await app_client.post(
        "/api/admin/fonogramas",
        json={
            "clave_fonograma": 1,
            "titulo": "Test",# tolerated (Pydantic allows extra fields with default config if not forbidden)
        },
    )
    assert response.status_code == 403  # editor required


@pytest.mark.asyncio
async def test_admin_fonograma_crud_roundtrip(db_session, app_client):
    await make_admin()
    await make_user(
        username="editor", email="editor@cenidim.example", role="editor"
    )
    await login_as(app_client, "editor", "Strong1234")

    # Create
    response = await app_client.post(
        "/api/admin/fonogramas",
        json={
            "clave_fonograma": 100,
            "titulo": "Album Test",
            "subtitulo": "Sub",
            "anio": "1950",# tolerated (Pydantic allows extra fields with default config if not forbidden)
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["clave_fonograma"] == 100

    # Read one
    response = await app_client.get("/api/admin/fonogramas/100")
    assert response.status_code == 200
    assert response.json()["titulo"] == "Album Test"

    # Read 404
    response = await app_client.get("/api/admin/fonogramas/999")
    assert response.status_code == 404

    # Update
    response = await app_client.put(
        "/api/admin/fonogramas/100",
        json={
            "clave_fonograma": 100,
            "titulo": "Album Test Renamed",
            "anio": "1951",},
    )
    assert response.status_code == 200, response.text
    assert response.json()["titulo"] == "Album Test Renamed"
    assert response.json()["anio"] == "1951"

    # List paginated
    response = await app_client.get("/api/admin/fonogramas?limit=10&page=1")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any(item["clave_fonograma"] == 100 for item in body["results"])

    # Delete (editor -> admin role required; re-login)
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.delete("/api/admin/fonogramas/100")
    assert response.status_code == 200
    response = await app_client.delete("/api/admin/fonogramas/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_fonograma_duplicate_returns_409(db_session, app_client):
    await make_admin()
    await make_user(
        username="editor", email="editor@cenidim.example", role="editor"
    )
    await login_as(app_client, "editor", "Strong1234")
    payload = {
        "clave_fonograma": 200,
        "titulo": "First",# tolerated (Pydantic allows extra fields with default config if not forbidden)
    }
    response = await app_client.post("/api/admin/fonogramas", json=payload)
    assert response.status_code == 201
    response = await app_client.post("/api/admin/fonogramas", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_admin_song_crud_roundtrip(db_session, app_client):
    await make_admin()
    await make_user(
        username="editor", email="editor@cenidim.example", role="editor"
    )
    await login_as(app_client, "editor", "Strong1234")

    # Seed a fonograma first so the FK target exists.
    response = await app_client.post(
        "/api/admin/fonogramas",
        json={"clave_fonograma": 300, "titulo": "Album",},
    )
    assert response.status_code == 201

    # Create a song
    response = await app_client.post(
        "/api/admin/songs",
        json={
            "fonograma_id": 300,
            "title": "Track One",
            "lyrics": "la la la",
        },
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["title"] == "Track One"
    assert created["id"] > 0
    assert created["fonograma_id"] == 300

    # List songs (joined view should include album + year).
    response = await app_client.get("/api/admin/songs")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    first = body["results"][0]
    assert first["title"] == "Track One"
    assert first["album"] == "Album"

    # Filter by fonograma_id
    response = await app_client.get("/api/admin/songs?fonograma_id=300")
    assert response.status_code == 200
    assert response.json()["total"] >= 1

    response = await app_client.get("/api/admin/songs?fonograma_id=999")
    assert response.status_code == 200
    assert response.json()["total"] == 0

    # Update song (only the editable fields)
    response = await app_client.put(
        "/api/admin/songs/1",
        json={
            "title": "Track One (Remastered)",
            "lyrics": "la la la la",
        },
    )
    assert response.status_code == 200, response.text

    # Delete via admin role
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.delete("/api/admin/songs/1")
    assert response.status_code == 200
    response = await app_client.delete("/api/admin/songs/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_song_update_404(db_session, app_client):
    await make_admin()
    await make_user(
        username="editor", email="editor@cenidim.example", role="editor"
    )
    await login_as(app_client, "editor", "Strong1234")
    response = await app_client.put(
        "/api/admin/songs/9999",
        json={
            "title": "X",
            "lyrics": None,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_fonograma_update_404(db_session, app_client):
    await make_admin()
    await make_user(
        username="editor", email="editor@cenidim.example", role="editor"
    )
    await login_as(app_client, "editor", "Strong1234")
    response = await app_client.put(
        "/api/admin/fonogramas/9999",
        json={
            "clave_fonograma": 9999,
            "titulo": "Ghost",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_user_update_404(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.put(
        "/api/admin/users/9999",
        json={"role": "viewer"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_user_update_weak_password(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    new_user = await make_user(
        username="victim", email="victim@cenidim.example", role="viewer"
    )
    response = await app_client.put(
        f"/api/admin/users/{new_user.id}",
        json={"password": "nodigits"},
    )
    assert response.status_code == 400
    assert "digit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_audit_log_filters(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    # Create a user (generates an audit row).
    response = await app_client.post(
        "/api/admin/users",
        json={
            "username": "audit-target",
            "email": "audit-target@cenidim.example",
            "password": "Strong1234",
        },
    )
    assert response.status_code == 201

    # Filter by action
    response = await app_client.get(
        "/api/admin/audit?action=user.create"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all(r["action"] == "user.create" for r in body["results"])

    # Filter by actor (the admin user we logged in as).
    response = await app_client.get("/api/admin/audit?actor_id=1")
    assert response.status_code == 200
    assert response.json()["total"] >= 1


@pytest.mark.asyncio
async def test_admin_user_update_no_fields(db_session, app_client):
    """Updating with no body fields just bumps the version."""
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    new_user = await make_user(
        username="noop", email="noop@cenidim.example", role="viewer"
    )
    response = await app_client.put(
        f"/api/admin/users/{new_user.id}",
        json={},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_emails_only_failures_filter(db_session, app_client):
    await make_admin()
    await make_email_outbox(to_addr="bob@cenidim.example", kind="password_reset")
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.get("/api/admin/emails?only_failures=true")
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_admin_user_crud_roundtrip(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")

    # List (initially contains the admin we just seeded)
    response = await app_client.get("/api/admin/users")
    assert response.status_code == 200
    assert any(u["username"] == "admin" for u in response.json())

    # Create a new editor
    response = await app_client.post(
        "/api/admin/users",
        json={
            "username": "carol",
            "email": "carol@cenidim.example",
            "password": "Strong1234",
            "role": "editor",
        },
    )
    assert response.status_code == 201, response.text
    user_id = response.json()["user"]["id"]

    # Duplicate username → 409
    response = await app_client.post(
        "/api/admin/users",
        json={
            "username": "carol",
            "email": "carol2@cenidim.example",
            "password": "Strong1234",
        },
    )
    assert response.status_code == 409

    # Update role only
    response = await app_client.put(
        f"/api/admin/users/{user_id}",
        json={"role": "viewer"},
    )
    assert response.status_code == 200

    # Delete
    response = await app_client.delete(f"/api/admin/users/{user_id}")
    assert response.status_code == 200

    # Delete unknown user → 404
    response = await app_client.delete("/api/admin/users/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_user_weak_password_rejected(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.post(
        "/api/admin/users",
        json={
            "username": "weak",
            "email": "weak@cenidim.example",
            "password": "nodigits",
        },
    )
    assert response.status_code == 400
    assert "digit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_cannot_delete_last_admin(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.delete("/api/admin/users/1")
    assert response.status_code == 400
    assert "last admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_unlink_identity(db_session, app_client):
    await make_admin()
    await make_identity(user_id=1, subject="google-subject-123")
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.delete("/api/admin/users/1/identity")
    assert response.status_code == 204
    response = await app_client.delete("/api/admin/users/1/identity")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_unlink_identity_invalid_id(app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")
    response = await app_client.delete("/api/admin/users/notint/identity")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_audit_log_records_creates(db_session, app_client):
    await make_admin()
    await login_as(app_client, "admin", "admin1234")

    response = await app_client.post(
        "/api/admin/users",
        json={
            "username": "audituser",
            "email": "audit@cenidim.example",
            "password": "Strong1234",
        },
    )
    assert response.status_code == 201

    response = await app_client.get("/api/admin/audit")
    assert response.status_code == 200
    body = response.json()
    actions = [row["action"] for row in body["results"]]
    assert "user.create" in actions


@pytest.mark.asyncio
async def test_admin_emails_endpoint(db_session, app_client):
    await make_admin()
    await make_email_outbox(to_addr="bob@cenidim.example", kind="password_reset")
    await login_as(app_client, "admin", "admin1234")

    response = await app_client.get("/api/admin/emails")
    assert response.status_code == 200
    assert response.json()["total"] >= 1
    assert response.json()["results"][0]["kind"] == "password_reset"

    response = await app_client.get(
        "/api/admin/emails?only_failures=true"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0
