"""SQLAlchemy 2.0 declarative base + naming conventions.

All model classes import ``Base`` from this module. Column names use
``snake_case`` so the SQL schema matches the existing Go layout 1:1;
this avoids any migration step from ``letras.db`` produced by the
Go ``cmd/build-db`` binary to the new Python schema.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base shared by every model."""

    __tablename__: str  # populated by subclasses


class TimestampMixin:
    """Adds created_at / version columns used by the existing schema.

    The Go schema has ``created_at DATETIME DEFAULT CURRENT_TIMESTAMP``
    on most tables and ``version INTEGER DEFAULT 0`` for optimistic
    locking on songs. We replicate those defaults here.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.current_timestamp(),
        nullable=False,
    )


__all__ = ["Base", "TimestampMixin"]
