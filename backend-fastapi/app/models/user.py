"""User model.

Mirrors the Go ``users`` table: id, username, email, password_hash,
role (viewer | editor | admin), created_at. The Go schema also has
``last_sign_in_method`` and ``last_sign_in_at`` from migration 004.
``version`` is added for optimistic locking (kept from the Go schema).
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.password_reset_token import PasswordResetToken
    from app.models.user_identity import UserIdentity


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="viewer")
    last_sign_in_method: Mapped[str | None] = mapped_column(String, nullable=True)
    last_sign_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    identities: Mapped[list[UserIdentity]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


__all__ = ["User"]
