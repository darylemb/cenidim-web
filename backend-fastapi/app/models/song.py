"""Song model.

Mirrors the Go ``songs`` table. Foreign key to ``fonogramas`` with
``ON DELETE CASCADE`` matches the migration the Go backend applies.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.fonograma import Fonograma
    from app.models.song_stats import SongStats


class Song(Base, TimestampMixin):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fonograma_id: Mapped[int] = mapped_column(
        ForeignKey("fonogramas.clave_fonograma", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    lyrics: Mapped[str | None] = mapped_column(String, nullable=True)
    clasificacion: Mapped[str | None] = mapped_column(String, nullable=True)
    tema: Mapped[str | None] = mapped_column(String, nullable=True)
    autor: Mapped[str | None] = mapped_column(String, nullable=True)
    compositor: Mapped[str | None] = mapped_column(String, nullable=True)
    duracion: Mapped[str | None] = mapped_column(String, nullable=True)
    personajes: Mapped[str | None] = mapped_column(String, nullable=True)
    temas_raw: Mapped[str | None] = mapped_column(String, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    fonograma: Mapped["Fonograma"] = relationship(back_populates="songs")
    stats: Mapped["SongStats | None"] = relationship(
        back_populates="song",
        cascade="all, delete-orphan",
        uselist=False,
    )


__all__ = ["Song"]
