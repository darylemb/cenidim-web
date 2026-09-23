"""Tests for app/deps.py: auth dependency edge cases."""
from __future__ import annotations

import pytest
from jose import jwt

from app import db as db_module
from app.config import Settings
from app.deps import _decode_jwt, get_current_user, require_role
from app.models import User


def _session():
    return db_module.session.get_sessionmaker()()


@pytest.mark.asyncio
async def test_decode_jwt_invalid_signature_raises_401(db_session, tmp_path):
    from fastapi import HTTPException

    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "x.db")
    bad_token = jwt.encode({"sub": "1"}, "wrong-secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        _decode_jwt(bad_token, settings)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_decode_jwt_expired_raises_401(db_session, tmp_path):
    from datetime import UTC, datetime, timedelta

    from fastapi import HTTPException

    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "x.db")
    past = datetime.now(UTC) - timedelta(seconds=3600)
    expired = jwt.encode(
        {"sub": "1", "exp": int(past.timestamp())},
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc:
        _decode_jwt(expired, settings)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_via_authorization_header(db_session, settings):
    from app.security import hash_password

    async with _session() as session:
        user = User(
            username="alice",
            email="alice@cenidim.example",
            password_hash=hash_password("Strong1234"),
            role="viewer",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        uid = user.id

    async with _session() as session:
        token = jwt.encode(
            {"sub": str(uid), "role": "viewer", "type": "access"},
            settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )
        from starlette.requests import Request

        req = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/api/admin/users",
                "headers": [(b"authorization", f"Bearer {token}".encode())],
                "query_string": b"",
            }
        )
        got = await get_current_user(req, session, settings)
        assert got.id == uid


@pytest.mark.asyncio
async def test_get_current_user_no_token_raises_401(db_session, settings):
    from fastapi import HTTPException
    from starlette.requests import Request

    req = Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/api/admin/users",
            "headers": [],
            "query_string": b"",
        }
    )
    async with _session() as session:
        with pytest.raises(HTTPException) as exc:
            await get_current_user(req, session, settings)
        assert exc.value.status_code == 401
        assert "Missing authentication" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_user_unknown_id_raises_401(db_session, settings):
    from fastapi import HTTPException
    from starlette.requests import Request

    async with _session() as session:
        token = jwt.encode(
            {"sub": "9999", "role": "admin", "type": "access"},
            settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )
        req = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/api/admin/users",
                "headers": [(b"authorization", f"Bearer {token}".encode())],
                "query_string": b"",
            }
        )
        with pytest.raises(HTTPException) as exc:
            await get_current_user(req, session, settings)
        assert exc.value.status_code == 401
        assert "User no longer exists" in exc.value.detail


@pytest.mark.asyncio
async def test_require_role_blocks_lower_tier(db_session):
    """Viewer is below editor; editor dep should reject them."""
    from fastapi import HTTPException

    from app.security import hash_password

    async with _session() as session:
        user = User(
            username="v",
            email="v@cenidim.example",
            password_hash=hash_password("Strong1234"),
            role="viewer",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        v = user
    dep = require_role("editor")
    with pytest.raises(HTTPException) as exc:
        await dep(v)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_role_passes_higher_tier(db_session):
    from app.security import hash_password

    async with _session() as session:
        user = User(
            username="a",
            email="a@cenidim.example",
            password_hash=hash_password("Strong1234"),
            role="admin",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        a = user
    dep = require_role("editor")
    result = await dep(a)
    assert result is a


@pytest.mark.asyncio
async def test_require_role_unknown_role_in_user(db_session):
    from fastapi import HTTPException

    from app.security import hash_password

    async with _session() as session:
        user = User(
            username="x",
            email="x@cenidim.example",
            password_hash=hash_password("Strong1234"),
            role="mystery",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        m = user
    dep = require_role("viewer")
    with pytest.raises(HTTPException) as exc:
        await dep(m)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_via_session_cookie(db_session, settings):
    """The ``cenidim_session`` cookie is preferred over the
    ``Authorization`` header when both are sent.
    """
    from app.security import hash_password

    async with _session() as session:
        user = User(
            username="cookied",
            email="cookied@cenidim.example",
            password_hash=hash_password("Strong1234"),
            role="viewer",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        uid = user.id

    async with _session() as session:
        cookie_token = jwt.encode(
            {"sub": str(uid), "role": "viewer", "type": "access"},
            settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )
        bearer_token = jwt.encode(
            {"sub": "9999999", "role": "viewer", "type": "access"},
            settings.jwt_secret.get_secret_value(),
            algorithm="HS256",
        )
        from starlette.requests import Request

        req = Request(
            scope={
                "type": "http",
                "method": "GET",
                "path": "/api/admin/users",
                "headers": [
                    (
                        b"cookie",
                        f"cenidim_session={cookie_token}".encode(),
                    ),
                    (
                        b"authorization",
                        f"Bearer {bearer_token}".encode(),
                    ),
                ],
                "query_string": b"",
            }
        )
        got = await get_current_user(req, session, settings)
        # Cookie wins -> we get our user, not the bearer user.
        assert got.id == uid
