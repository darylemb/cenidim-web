"""Tests for app.db.session: engine lifecycle + session_scope CM."""
from __future__ import annotations

import pytest

from app import db as db_module
from app.config import Settings
from app.db import dispose_engine, session_scope, session_scope_cm
from app.db.session import init_engine, init_in_memory_engine


def _engine():
    """Read the current engine via the module to avoid the
    Python-binding-cache trap (``from ... import _engine`` snapshots
    the original ``None``).
    """
    return db_module.session._engine


def _sessionmaker():
    return db_module.session._sessionmaker


def test_init_engine_creates_sessionmaker(tmp_path):
    init_engine(
        Settings(env="dev", db_path=tmp_path / "x.db", jwt_secret="x" * 64)
    )
    e = _engine()
    sm = _sessionmaker()
    assert e is not None
    assert sm is not None
    assert str(tmp_path / "x.db") in str(e.url)


def test_init_in_memory_engine_uses_static_pool():
    e = init_in_memory_engine()
    assert e is not None
    # StaticPool is the only sane choice for in-memory with multiple connections.
    assert e.pool.__class__.__name__ == "StaticPool"


@pytest.mark.asyncio
async def test_dispose_engine_clears_globals():
    init_in_memory_engine()
    assert _engine() is not None
    await dispose_engine()
    assert _engine() is None


@pytest.mark.asyncio
async def test_dispose_engine_noop_when_unset():
    """Calling dispose without a configured engine must not raise."""
    db_module.session._engine = None
    db_module.session._sessionmaker = None
    await dispose_engine()
    assert _engine() is None


def test_get_sessionmaker_creates_on_demand(tmp_path):
    db_module.session._engine = None
    db_module.session._sessionmaker = None
    sm = db_module.session.get_sessionmaker()
    assert sm is not None
    assert _engine() is not None


@pytest.mark.asyncio
async def test_session_scope_cm_commits_on_clean_exit():
    init_in_memory_engine()
    async with session_scope_cm() as session:
        from sqlalchemy import text as sa_text

        await session.execute(sa_text("CREATE TABLE t (x INTEGER)"))
        await session.execute(sa_text("INSERT INTO t VALUES (42)"))

    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import text as sa_text

        result = (await session.execute(sa_text("SELECT x FROM t"))).scalar_one()
        assert result == 42


@pytest.mark.asyncio
async def test_session_scope_cm_rolls_back_on_exception():
    init_in_memory_engine()
    # Seed a table inside its own committed CM so DDL is durable.
    async with session_scope_cm() as session:
        from sqlalchemy import text as sa_text

        await session.execute(sa_text("CREATE TABLE t (x INTEGER)"))

    with pytest.raises(RuntimeError):
        async with session_scope_cm() as session:
            from sqlalchemy import text as sa_text

            await session.execute(sa_text("INSERT INTO t VALUES (1)"))
            raise RuntimeError("boom")

    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import text as sa_text

        result = (
            await session.execute(sa_text("SELECT COUNT(*) FROM t"))
        ).scalar_one()
        # The INSERT inside the rolled-back CM must not have persisted.
        assert result == 0


@pytest.mark.asyncio
async def test_session_scope_generator_commit_path():
    """Bare session_scope() (used inside FastAPI deps) commits on success."""
    init_in_memory_engine()
    gen = session_scope()
    sess = await gen.__anext__()
    from sqlalchemy import text as sa_text

    await sess.execute(sa_text("CREATE TABLE g (v INTEGER)"))
    await sess.execute(sa_text("INSERT INTO g VALUES (1)"))
    with pytest.raises(StopAsyncIteration):
        await gen.__anext__()

    sm = db_module.session.get_sessionmaker()
    async with sm() as session2:
        from sqlalchemy import text as sa_text2

        result = (await session2.execute(sa_text2("SELECT v FROM g"))).scalar_one()
        assert result == 1
