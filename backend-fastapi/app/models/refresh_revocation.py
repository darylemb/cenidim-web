"""Refresh-token revocation list (logout / rotate).

Phase 1 uses HttpOnly cookies for both access + refresh tokens.
Whenever the access token is refreshed we revoke the old refresh jti
and store a row here so a stolen cookie cannot be replayed after the
user logs out from another device.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RefreshTokenRevocation(Base):
    __tablename__ = "refresh_token_revocations"

    jti: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.current_timestamp(),
    )


__all__ = ["RefreshTokenRevocation"]
