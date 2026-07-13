"""Tests for app/main.py: app factory, middleware, routers, /healthz."""
from __future__ import annotations

import importlib

import pytest

from app.config import Settings


@pytest.fixture
def reload_app_module(monkeypatch):
    """Reload app.main with a fresh Settings so create_app() runs cleanly."""
    import app.main

    importlib.reload(app.main)
    yield app.main


def test_create_app_returns_fastapi_instance(tmp_path):
    from fastapi import FastAPI

    from app.main import create_app

    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "x.db")
    app = create_app(settings)
    assert isinstance(app, FastAPI)
    assert app.title == settings.app_name


def test_module_level_app_exists():
    """`uvicorn app.main:app` needs a module-level ASGI app."""
    import app.main

    assert hasattr(app.main, "app")
    from fastapi import FastAPI

    assert isinstance(app.main.app, FastAPI)


def test_dev_startup_creates_schema_when_db_empty(tmp_path, monkeypatch):
    """The dev-mode bootstrap creates the schema for an empty DB."""
    import asyncio

    monkeypatch.setenv("CENIDIM_ENV", "dev")
    monkeypatch.setenv("CENIDIM_DB_PATH", str(tmp_path / "bootstrap.db"))
    monkeypatch.setenv("CENIDIM_JWT_SECRET", "x" * 64)
    # Reset cached Settings + dispose any existing engine.
    from app import config as cfg_module
    from app import db as db_module

    cfg_module.get_settings.cache_clear()

    async def _dispose() -> None:
        await db_module.dispose_engine()

    asyncio.run(_dispose())
    db_module.session._engine = None
    db_module.session._sessionmaker = None

    from app.main import create_app

    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "bootstrap.db")
    app = create_app(settings)

    # Trigger the lifespan startup.
    import asyncio

    async def _drive():
        async with app.router.lifespan_context(app):
            from sqlalchemy import inspect
            from sqlalchemy import text as sa_text

            from app.db import init_engine

            engine = init_engine(settings)

            def _list_tables(sync_conn):
                return set(inspect(sync_conn).get_table_names())

            async with engine.connect() as conn:
                names = await conn.run_sync(_list_tables)
            assert "users" in names
            assert "songs" in names
            assert "fonogramas" in names
            async with engine.begin() as conn:
                count = (await conn.execute(sa_text("SELECT COUNT(*) FROM users"))).scalar_one()
            assert count == 0

    asyncio.run(_drive())


def test_dev_startup_skips_when_tables_exist(tmp_path):
    """If the DB already has tables, dev startup leaves it alone (no
    ``create_all`` clobbering existing data).
    """
    import asyncio

    from sqlalchemy import text as sa_text

    from app.db import init_engine
    from app.main import create_app
    from app.models import Base

    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "exists.db")
    e = init_engine(settings)

    async def _seed():
        async with e.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(
                sa_text(
                    "INSERT INTO users (username, email, password_hash, role, version) "
                    "VALUES ('alice', 'a@x.example', 'h', 'viewer', 0)"
                )
            )

    asyncio.run(_seed())

    app = create_app(settings)

    async def _drive():
        async with app.router.lifespan_context(app):
            from sqlalchemy import inspect

            from app.db import init_engine as _init

            engine = _init(settings)

            def _list_tables(sync_conn):
                return set(inspect(sync_conn).get_table_names())

            async with engine.connect() as conn:
                names = await conn.run_sync(_list_tables)
            assert "users" in names
            async with engine.connect() as conn:
                count = (
                    await conn.execute(sa_text("SELECT COUNT(*) FROM users"))
                ).scalar_one()
            assert count == 1  # not clobbered

    asyncio.run(_drive())
