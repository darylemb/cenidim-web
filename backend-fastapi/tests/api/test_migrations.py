"""Integration test for the FastAPI-managed tables migration.

The original ``initial_schema`` migration (96f3e399e38d) was written
as a no-op when the Go-seeded legacy tables already exist, but the
follow-up migration (f6f8e399e38d) only adds columns — it never
creates the FastAPI-only tables (``audit_log``, ``email_outbox``,
``password_reset_tokens``, ``refresh_token_revocations``,
``user_identities``). The new migration closes that gap.

This test runs alembic against a fresh sqlite file in three states:

1. Empty DB — all five FastAPI tables must be created.
2. Legacy-only DB (Go-seeded shape: only ``fonogramas``, ``songs``,
   ``users``, ``song_stats``) — the five FastAPI tables must be
   added and the legacy tables must be left alone.
3. FastAPI-native DB (everything already exists) — the migration
   must be a no-op.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command

_FASTAPI_TABLES = frozenset(
    {
        "audit_log",
        "email_outbox",
        "password_reset_tokens",
        "refresh_token_revocations",
        "user_identities",
    }
)


@pytest.fixture
def alembic_cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    """Alembic config pointed at a fresh sqlite file.

    We deliberately do NOT call ``Config(str(alembic.ini))`` because
    the ini's ``[loggers]`` section triggers ``logging.fileConfig``,
    which resets the root logger and breaks ``caplog`` for any
    later test in the same session (see
    test_enqueue_respects_provider_off_and_dev_print).
    """
    db_path = tmp_path / "alembic_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    repo_root = Path(__file__).resolve().parents[2]
    cfg = Config()
    cfg.set_main_option("script_location", str(repo_root / "alembic"))
    return cfg


def _table_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


def test_migration_creates_fastapi_tables_on_empty_db(
    alembic_cfg: Config, tmp_path: Path
) -> None:
    db_path = tmp_path / "alembic_test.db"
    command.upgrade(alembic_cfg, "head")

    names = _table_names(db_path)
    assert _FASTAPI_TABLES.issubset(names)


def test_migration_creates_fastapi_tables_on_go_seeded_db(
    alembic_cfg: Config, tmp_path: Path
) -> None:
    """Production cutover scenario: the DB has only the Go legacy
    tables. After alembic upgrade head, the FastAPI tables must be
    present alongside them (no legacy DDL)."""
    db_path = tmp_path / "alembic_test.db"

    # Pre-create the Go legacy schema so the first migration (the
    # no-op branch) takes over.
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
            CREATE TABLE fonogramas (
                clave_fonograma INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                anio TEXT,
                version INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fonograma_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                filename TEXT,
                lyrics TEXT,
                clasificacion TEXT,
                tema TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                version INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(fonograma_id) REFERENCES fonogramas(clave_fonograma)
            );
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                version INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE song_stats (
                song_id INTEGER PRIMARY KEY,
                pct_oov REAL NOT NULL,
                categoria TEXT NOT NULL,
                contiene_indigena INTEGER NOT NULL,
                n_tokens INTEGER NOT NULL,
                FOREIGN KEY(song_id) REFERENCES songs(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

    command.upgrade(alembic_cfg, "head")

    names = _table_names(db_path)
    # Legacy Go tables must be untouched.
    assert {"fonogramas", "songs", "users", "song_stats"}.issubset(names)
    # FastAPI tables must now exist.
    assert _FASTAPI_TABLES.issubset(names)


def test_migration_is_noop_on_fastapi_native_db(
    alembic_cfg: Config, tmp_path: Path
) -> None:
    """Run the upgrade once to populate a complete FastAPI-native DB,
    then run it a second time and confirm no errors and no tables
    dropped."""
    db_path = tmp_path / "alembic_test.db"

    command.upgrade(alembic_cfg, "head")
    first_pass = _table_names(db_path)
    command.upgrade(alembic_cfg, "head")
    second_pass = _table_names(db_path)

    # Alembic should not drop or recreate anything on a clean
    # second pass.
    assert first_pass == second_pass
    assert _FASTAPI_TABLES.issubset(second_pass)


def test_new_migration_chains_off_metadata_columns_migration(
    alembic_cfg: Config, tmp_path: Path
) -> None:
    """The new migration's ``down_revision`` must point at
    ``f6f8e399e38d`` (the previous head) so the alembic history
    forms a single linear chain from a Go-seeded DB."""
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(alembic_cfg)
    rev = script.get_revision("a1b2c3d4e5f6")
    assert rev is not None
    assert rev.down_revision == "f6f8e399e38d"


def test_refresh_token_revocations_table_supports_jti_lookup(
    alembic_cfg: Config, tmp_path: Path
) -> None:
    """The migration must create a UNIQUE index on ``jti`` so the
    auth dependency's ``SELECT ... WHERE jti = ?`` works (and the
    duplicate-rotation guard at write time raises IntegrityError)."""
    db_path = tmp_path / "alembic_test.db"
    command.upgrade(alembic_cfg, "head")

    conn = sqlite3.connect(str(db_path))
    try:
        indexes = conn.execute(
            "SELECT name, sql FROM sqlite_master "
            "WHERE type='index' AND tbl_name='refresh_token_revocations'"
        ).fetchall()
        names = {row[0] for row in indexes}
        # The SQLAlchemy ``unique=True`` on the column produces an
        # auto-named index; the explicit ``ix_refresh_token_revocations_jti``
        # covers the same column. At least one of them must be unique.
        assert any("UNIQUE" in (row[1] or "").upper() for row in indexes) or any(
            "autoindex" in n.lower() for n in names
        )
    finally:
        conn.close()
