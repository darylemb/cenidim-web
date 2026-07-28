"""create FastAPI-managed tables (audit_log, email_outbox, password_reset_tokens, refresh_token_revocations, user_identities)

Revision ID: a1b2c3d4e5f6
Revises: f6f8e399e38d
Create Date: 2026-07-28 07:00:00.000000

The original ``initial_schema`` migration (96f3e399e38d) was written
as a no-op when the Go-seeded legacy tables already exist, on the
assumption that a separate code path would create the FastAPI-only
tables. That code path never materialised, so a Go-seeded
``letras.db`` is missing ``audit_log``, ``email_outbox``,
``password_reset_tokens``, ``refresh_token_revocations``, and
``user_identities`` after the alembic stamp lands at
``f6f8e399e38d``.

The first authenticated request that touches
``refresh_token_revocations`` (e.g. ``POST /api/auth/refresh``) then
crashes with::

    sqlalchemy.exc.OperationalError: no such table: refresh_token_revocations

This migration is purely additive: it creates the five FastAPI-only
tables IF they do not already exist (so a fresh DB, where the
original migration created them, is a no-op; and a Go-seeded DB
gets them).

The DDL matches what ``initial_schema`` would have emitted on a
fresh DB; the column types and constraints are kept identical so
SQLAlchemy's ORM models bind cleanly.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f6f8e399e38d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables owned by the FastAPI ORM (not present in a Go-seeded DB).
_FASTAPI_TABLES = frozenset(
    {
        "audit_log",
        "email_outbox",
        "password_reset_tokens",
        "refresh_token_revocations",
        "user_identities",
    }
)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if "audit_log" not in existing:
        op.create_table(
            "audit_log",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=64), nullable=False),
            sa.Column("target_type", sa.String(length=64), nullable=True),
            sa.Column("target_id", sa.Integer(), nullable=True),
            sa.Column("detail", sa.String(), nullable=True),
            sa.Column("ip", sa.String(length=64), nullable=True),
            sa.Column(
                "occurred_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_audit_log_action", "audit_log", ["action"], unique=False)
        op.create_index(
            "ix_audit_log_actor_id", "audit_log", ["actor_id"], unique=False
        )
        op.create_index(
            "ix_audit_log_occurred_at",
            "audit_log",
            ["occurred_at"],
            unique=False,
        )

    if "email_outbox" not in existing:
        op.create_table(
            "email_outbox",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("to_addr", sa.String(), nullable=False),
            sa.Column("subject", sa.String(), nullable=False),
            sa.Column("body_text", sa.String(), nullable=False),
            sa.Column("body_html", sa.String(), nullable=True),
            sa.Column("kind", sa.String(), nullable=False),
            sa.Column("related_user_id", sa.Integer(), nullable=True),
            sa.Column("delivered_at", sa.DateTime(), nullable=True),
            sa.Column("failed_at", sa.DateTime(), nullable=True),
            sa.Column("failure_reason", sa.String(), nullable=True),
            sa.Column(
                "sent_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["related_user_id"], ["users.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_email_outbox_kind", "email_outbox", ["kind"], unique=False)
        op.create_index(
            "ix_email_outbox_related_user_id",
            "email_outbox",
            ["related_user_id"],
            unique=False,
        )
        op.create_index(
            "ix_email_outbox_to_addr", "email_outbox", ["to_addr"], unique=False
        )

    if "password_reset_tokens" not in existing:
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
        )
        op.create_index(
            "ix_password_reset_tokens_user_id",
            "password_reset_tokens",
            ["user_id"],
            unique=False,
        )

    if "refresh_token_revocations" not in existing:
        op.create_table(
            "refresh_token_revocations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("jti", sa.String(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("reason", sa.String(length=64), nullable=False),
            sa.Column(
                "revoked_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("jti"),
        )
        op.create_index(
            "ix_refresh_revocations_expires_at",
            "refresh_token_revocations",
            ["expires_at"],
            unique=False,
        )
        op.create_index(
            "ix_refresh_token_revocations_jti",
            "refresh_token_revocations",
            ["jti"],
            unique=True,
        )
        op.create_index(
            "ix_refresh_token_revocations_user_id",
            "refresh_token_revocations",
            ["user_id"],
            unique=False,
        )

    if "user_identities" not in existing:
        op.create_table(
            "user_identities",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("provider", sa.String(length=32), nullable=False),
            sa.Column("subject", sa.String(), nullable=False),
            sa.Column("email_at_link", sa.String(), nullable=False),
            sa.Column(
                "linked_at",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "provider", "subject", name="uq_user_identities_provider_subject"
            ),
        )
        op.create_index(
            "ix_user_identities_user_id",
            "user_identities",
            ["user_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    # Drop the FastAPI-only tables; leave the legacy Go-seeded tables
    # alone (the Go db-init recreates them on next boot).
    for table in (
        "user_identities",
        "refresh_token_revocations",
        "password_reset_tokens",
        "email_outbox",
        "audit_log",
    ):
        if table in existing and table in _FASTAPI_TABLES:
            op.drop_table(table)