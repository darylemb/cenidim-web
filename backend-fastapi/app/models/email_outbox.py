"""Email outbox.

Phase 1 persists every "sent" email here regardless of provider. When
Resend is configured and accepts, ``delivered_at`` is set; otherwise
the row stays open so the admin UI can re-send manually.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class EmailOutbox(Base):
    __tablename__ = "email_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    to_addr: Mapped[str] = mapped_column(String, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body_text: Mapped[str] = mapped_column(String, nullable=False)
    body_html: Mapped[str | None] = mapped_column(String, nullable=True)
    kind: Mapped[str] = mapped_column(String, nullable=False, index=True)
    related_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    failure_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    user: Mapped[User | None] = relationship(foreign_keys=[related_user_id])


__all__ = ["EmailOutbox"]
