"""Refresh-token revocation table.

Stores the ``jti`` of every issued refresh token until it would have
expired (TTL + grace). Calling ``is_revoked(jti)`` consults this table
during the auth dependency; on a hit the refresh is rejected with 401.
This is the fallback in case a stolen refresh token cannot be
short-circuited by the secure cookie flags.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RefreshTokenRevocation(Base):
    __tablename__ = "refresh_token_revocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(64), nullable=False, default="rotated")
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False
    )

    __table_args__ = (
        Index(
            "ix_refresh_revocations_expires_at",
            "expires_at",
        ),
    )


__all__ = ["RefreshTokenRevocation"]
