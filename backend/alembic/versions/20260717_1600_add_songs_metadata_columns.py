"""add songs metadata columns + user sign-in fields + fonogramas columns

Revision ID: f6f8e399e38d
Revises: 96f3e399e38d
Create Date: 2026-07-17 16:00:00.000000

The Go backend's ``cmd/build-db`` only creates the legacy column set
in ``songs``, ``fonogramas``, and ``users``. The FastAPI ORM models
declare additional columns (``autor``, ``compositor``, ``duracion``,
``personajes``, ``temas_raw``, ``editora``, ``last_sign_in_method``,
``last_sign_in_at``) that the FastAPI endpoints depend on. Without
this migration the dashboard's /api/search throws
``OperationalError: no such column: songs.autor`` against a
Go-seeded letras.db.

The migration is additive only — no destructive ``ALTER COLUMN`` /
``DROP COLUMN`` calls — so a re-run against a Go-only DB upgrades
cleanly and against an already-migrated DB is a no-op.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6f8e399e38d"
down_revision: Union[str, None] = "96f3e399e38d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # ---- songs: add FastAPI-only metadata columns ----
    if "songs" in existing_tables:
        songs_cols = {c["name"] for c in inspector.get_columns("songs")}
        with op.batch_alter_table("songs") as batch_op:
            for col, typedef in (
                ("autor", sa.String()),
                ("compositor", sa.String()),
                ("duracion", sa.String()),
                ("personajes", sa.String()),
                ("temas_raw", sa.String()),
            ):
                if col not in songs_cols:
                    batch_op.add_column(sa.Column(col, typedef, nullable=True))

    # ---- fonogramas: add ``editora`` (Phase 0+) ----
    if "fonogramas" in existing_tables:
        fono_cols = {c["name"] for c in inspector.get_columns("fonogramas")}
        with op.batch_alter_table("fonogramas") as batch_op:
            if "editora" not in fono_cols:
                batch_op.add_column(sa.Column("editora", sa.String(), nullable=True))

    # ---- users: add last_sign_in_* (Phase 0 migration 004) ----
    if "users" in existing_tables:
        users_cols = {c["name"] for c in inspector.get_columns("users")}
        with op.batch_alter_table("users") as batch_op:
            if "last_sign_in_method" not in users_cols:
                batch_op.add_column(sa.Column("last_sign_in_method", sa.String(), nullable=True))
            if "last_sign_in_at" not in users_cols:
                batch_op.add_column(sa.Column("last_sign_in_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" in existing_tables:
        with op.batch_alter_table("users") as batch_op:
            users_cols = {c["name"] for c in inspector.get_columns("users")}
            if "last_sign_in_at" in users_cols:
                batch_op.drop_column("last_sign_in_at")
            if "last_sign_in_method" in users_cols:
                batch_op.drop_column("last_sign_in_method")

    if "fonogramas" in existing_tables:
        fono_cols = {c["name"] for c in inspector.get_columns("fonogramas")}
        if "editora" in fono_cols:
            with op.batch_alter_table("fonogramas") as batch_op:
                batch_op.drop_column("editora")

    if "songs" in existing_tables:
        songs_cols = {c["name"] for c in inspector.get_columns("songs")}
        with op.batch_alter_table("songs") as batch_op:
            for col in ("temas_raw", "personajes", "duracion", "compositor", "autor"):
                if col in songs_cols:
                    batch_op.drop_column(col)
