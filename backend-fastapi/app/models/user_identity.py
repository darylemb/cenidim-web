"""UserIdentity: OAuth provider links.

Mirrors migration 004 in the Go backend: a single row per
(provider, subject) pair, plus the email that was current at link
time (so future email changes don't lose the audit trail).
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserIdentity(Base):
    __tablename__ = "user_identities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    email_at_link: Mapped[str] = mapped_column(String, nullable=False)
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    user: Mapped[User] = relationship(back_populates="identities")

    __table_args__ = (
        UniqueConstraint("provider", "subject", name="uq_user_identities_provider_subject"),
    )


__all__ = ["UserIdentity"]
