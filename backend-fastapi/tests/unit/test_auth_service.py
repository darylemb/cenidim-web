"""Auth service unit tests: register / login / password reset."""
from __future__ import annotations

import pytest

from app import db as db_module
from app.services.auth import (
    AuthError,
    authenticate,
    register_user,
)


def _session():
    """Hand back a fresh AsyncSession on the in-memory engine."""
    return db_module.session.get_sessionmaker()()


@pytest.mark.asyncio
async def test_register_user_happy_path(db_session, settings):
    async with _session() as session:
        user = await register_user(
            session,
            username="alice",
            email="alice@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        assert user.id is not None
        assert user.username == "alice"
        assert user.role == "viewer"


@pytest.mark.asyncio
async def test_register_user_rejects_weak_password(db_session, settings):
    async with _session() as session:
        with pytest.raises(AuthError) as exc:
            await register_user(
                session,
                username="bob",
                email="bob@cenidim.example",
                password="nodigits",
                settings=settings,
            )
        assert exc.value.status_code == 400
        assert "digit" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate(db_session, settings):
    async with _session() as session:
        await register_user(
            session,
            username="carol",
            email="carol@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        with pytest.raises(AuthError) as exc:
            await register_user(
                session,
                username="carol",
                email="carol@cenidim.example",
                password="Different1",
                settings=settings,
            )
        assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_authenticate_round_trip(db_session, settings):
    async with _session() as session:
        await register_user(
            session,
            username="dave",
            email="dave@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        user = await authenticate(session, username="dave", password="Strong1234")
        assert user.username == "dave"


@pytest.mark.asyncio
async def test_authenticate_rejects_bad_password(db_session, settings):
    async with _session() as session:
        await register_user(
            session,
            username="eve",
            email="eve@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        with pytest.raises(AuthError) as exc:
            await authenticate(
                session, username="eve", password="WrongPass1"
            )
        assert exc.value.status_code == 401
