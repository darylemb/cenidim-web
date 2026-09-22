"""Async SQLAlchemy 2.0 engine + session factory.

The schema is opened with WAL journal mode and a generous busy
timeout so a hung writer cannot deadlock readers. For tests we
expose a helper that swaps the engine for an in-memory aiosqlite DB
(``init_in_memory_engine``), which is what the test fixtures use.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator

from sqlalchemy import Engine, event
from sqlalchemy.ext.asyncio import (  # noqa: F401
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings

# SQLite's ``CAST('text' AS INTEGER)`` returns 0 for any string that
# doesn't start with a digit. The CSV's ``anio`` column has dirty
# values like ``[1982]`` and ``1965 (disco 1)...`` that would all
# collapse to 0 and sort before every real year. Register a Python
# UDF that mirrors the ``normalize_year`` helper in
# ``app.services.filters`` so SQL ORDER BY agrees with the JSON
# response.
_NORMALIZE_YEAR_RE = re.compile(r"(\d{4})")


def _normalize_year_py(raw: object) -> int:
    if raw is None:
        return 0
    s = str(raw).strip()
    if not s or s.lower() == "s/d":
        return 0
    m = _NORMALIZE_YEAR_RE.search(s)
    return int(m.group(1)) if m else 0


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

    @event.listens_for(_engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        # Register a Python UDF that normalizes the dirty ``anio``
        # column the same way the Python ``normalize_year`` helper
        # does. SQL ORDER BY uses this so ``[1982]`` sorts next to
        # the clean ``1982`` rows, not as 0.
        dbapi_connection.create_function(
            "normalize_year", 1, _normalize_year_py, deterministic=True
        )
        cursor.close()

    return _engine


def init_in_memory_engine() -> Engine:
    """Create an in-memory engine (test-only).

    Uses ``StaticPool`` so every connection shares the same underlying
    sqlite database (the default :memory: makes a fresh DB per
    connection, which breaks tests that seed via one connection and
    read via another).
    """
    from sqlalchemy.pool import StaticPool

    global _engine, _sessionmaker
    _engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)

    @event.listens_for(_engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        dbapi_connection.create_function(
            "normalize_year", 1, _normalize_year_py, deterministic=True
        )
        cursor.close()

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


class _SessionScopeCM:
    """Async-context-manager wrapper around ``session_scope()``.

    Some helpers outside the FastAPI dependency tree want to write
    through ``async with session_scope() as db:`` (matching the Go
    style). The FastAPI dep continues to use the bare async
    generator. Both forms share the same commit/rollback behaviour.
    """

    def __init__(self) -> None:
        self._gen = session_scope()
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> AsyncSession:
        self._session = await self._gen.__anext__()
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc is None:
            # Drive the generator to completion so the commit fires.
            try:
                await self._gen.__anext__()
            except StopAsyncIteration:
                pass
            return
        # Re-raise into the generator so its try/except can roll back.
        raised = None
        try:
            await self._gen.athrow(exc)
        except StopAsyncIteration:
            # Generator exited cleanly after rollback; nothing more.
            return
        except BaseException as propagated:
            raised = propagated
        # If athrow returned without raising, the generator is
        # exhausted or already yielded; treat as best-effort rollback.
        if raised is not None:
            raise raised


def session_scope_cm() -> _SessionScopeCM:
    """Return a fresh ``async with``-compatible CM around
    ``session_scope()``. Use it from non-FastAPI callers (e.g. the
    email service when no request-scoped session is available).
    """
    return _SessionScopeCM()


__all__ = [
    "init_engine",
    "init_in_memory_engine",
    "dispose_engine",
    "get_sessionmaker",
    "session_scope",
    "session_scope_cm",
]
