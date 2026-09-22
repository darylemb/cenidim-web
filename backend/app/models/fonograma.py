"""Fonograma (album) model.

Mirrors the Go ``fonogramas`` table. Column order and names match the
Go CREATE TABLE so this ORM maps cleanly to the existing schema.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.song import Song


class Fonograma(Base):
    __tablename__ = "fonogramas"

    clave_fonograma: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    subtitulo: Mapped[str | None] = mapped_column(String, nullable=True)
    interprete_principal: Mapped[str | None] = mapped_column(String, nullable=True)
    interpretes_invitados: Mapped[str | None] = mapped_column(String, nullable=True)
    interprete_participante: Mapped[str | None] = mapped_column(String, nullable=True)
    soporte_fisico: Mapped[str | None] = mapped_column(String, nullable=True)
    editora: Mapped[str | None] = mapped_column(String, nullable=True)
    numero_catalogo: Mapped[str | None] = mapped_column(String, nullable=True)
    ciudad_edicion: Mapped[str | None] = mapped_column(String, nullable=True)
    pais_edicion: Mapped[str | None] = mapped_column(String, nullable=True)
    anio: Mapped[str | None] = mapped_column(String, nullable=True)
    pistas: Mapped[str | None] = mapped_column(String, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(String, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    songs: Mapped[list[Song]] = relationship(back_populates="fonograma")


__all__ = ["Fonograma"]
