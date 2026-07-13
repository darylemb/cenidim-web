"""song_stats: per-song OOV metrics computed by classify_songs.py."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.song import Song


class SongStats(Base):
    __tablename__ = "song_stats"

    song_id: Mapped[int] = mapped_column(
        ForeignKey("songs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    pct_oov: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    categoria: Mapped[str] = mapped_column(String, nullable=False, default="")
    contiene_indigena: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    song: Mapped["Song"] = relationship(back_populates="stats")


__all__ = ["SongStats"]
