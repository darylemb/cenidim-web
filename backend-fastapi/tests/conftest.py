"""Pytest configuration and shared fixtures."""
from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio

from app.config import Settings
from app.db import init_in_memory_engine
from app.models import Base
from app.services.email import EmailService


@pytest_asyncio.fixture
async def settings(tmp_path) -> Settings:
    """Settings pointing at a fresh in-memory sqlite + tmp admin bootstrap."""
    return Settings(
        env="dev",
        db_path=tmp_path / "test.db",
        jwt_secret="test-secret-must-be-at-least-32-chars-long-xx",
        admin_bootstrap_username="admin",
        admin_bootstrap_email="admin@cenidim.test",
        admin_bootstrap_password="admin1234",
    )


@pytest_asyncio.fixture
async def db_session(settings: Settings) -> AsyncIterator:
    init_in_memory_engine()
    EmailService.configure(settings)
    # The in-memory DB starts empty; create_all() is idempotent.
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.db.session import _engine, get_sessionmaker

    if _engine is None:
        init_in_memory_engine()
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sm = get_sessionmaker()
    async with sm() as session:
        yield session
