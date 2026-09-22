"""Alembic environment.

Reads ``DATABASE_URL`` from the process environment so a single
``alembic.ini`` works for every target (docker, CI, local dev).

For synchronous SQLite (which is what we use here), we run
alembic in the default greenlet/threadpool mode. For async
engines the ``run_async_migrations`` helper would be used; we keep
the sync path for now because ``alembic`` itself is sync.
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make ``app`` importable when alembic is invoked from any cwd.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.models import Base  # noqa: E402  - re-exports the declarative base

# ``Base.metadata`` is the source of truth for ``--autogenerate``.
TARGET_METADATA = Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _resolve_url() -> str:
    """Pull the database URL from env (with sensible defaults).

    Alembic runs synchronously, so we strip the ``+aiosqlite``
    async driver and use the stock sqlite3 dialect for migrations.
    """
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return _to_sync_sqlite_url(env_url)
    settings = Settings()  # uses env-overridable defaults
    return _to_sync_sqlite_url(settings.db_url)


def _to_sync_sqlite_url(url: str) -> str:
    """Replace the aiosqlite driver with the stdlib sqlite3 driver.

    alembic is sync, so the async driver would otherwise blow up
    inside ``engine_from_config`` with a ``MissingGreenlet``.
    """
    if url.startswith("sqlite+aiosqlite:"):
        return "sqlite:" + url[len("sqlite+aiosqlite:"):]
    return url


def run_migrations_offline() -> None:
    """Run migrations without an active DB connection (emits SQL)."""
    context.configure(
        url=_resolve_url(),
        target_metadata=TARGET_METADATA,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _resolve_url()
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=TARGET_METADATA,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()