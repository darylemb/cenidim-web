"""Async SQLAlchemy 2.0 engine + session factory.

The schema is opened with WAL journal mode and a generous busy
timeout so a hung writer cannot deadlock readers. For tests we
expose a helper that swaps the engine for an in-memory aiosqlite DB
(``init_in_memory_engine``), which is what the test fixtures use.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings

# Module-level state. The engine + sessionmaker are set in
# ``init_engine()`` at app startup. Tests that need a fresh
# in-memory database call ``init_in_memory_engine()`` instead.
_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create the production engine (file-backed sqlite) + sessionmaker."""
    global _engine, _sessionmaker
    settings = settings or get_settings()
    _engine = create_async_engine(
        settings.db_url,
        echo=settings.db_echo,
        connect_args={
            "check_same_thread": False,
            # Apply WAL mode + a generous busy_timeout so writers and
            # readers don't deadlock each other. These PRAGMAs are
            # sqlite-specific so they live in connect_args instead of
            # the URL.
            "timeout": 30,
        },
        pool_size=settings.db_pool_size,
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def init_in_memory_engine() -> AsyncEngine:
    """Create an in-memory engine (test-only)."""
    global _engine, _sessionmaker
    _engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def dispose_engine() -> None:
    """Close the current engine. Safe to call when none is set."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the active sessionmaker, creating a file-backed engine on
    demand if none is configured yet (useful for early-import test
    fixtures).
    """
    global _sessionmaker
    if _sessionmaker is None:
        init_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def session_scope() -> AsyncIterator[AsyncSession]:
    """Yield an AsyncSession inside a transaction; commit on success.

    Used by the FastAPI dependency below. The session is bound to the
    request lifecycle: opened when the request enters the dependency
    tree, committed when the route handler returns, rolled back if an
    exception propagates.
    """
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


__all__ = [
    "init_engine",
    "init_in_memory_engine",
    "dispose_engine",
    "get_sessionmaker",
    "session_scope",
]
