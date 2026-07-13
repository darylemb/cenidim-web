"""Fonograma + Song Pydantic v2 schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.fonograma import Fonograma
from app.models.song import Song

ClaveFonograma = Annotated[int, Field(ge=1)]
SongId = Annotated[int, Field(ge=1)]


class FonogramaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clave_fonograma: int
    titulo: str
    subtitulo: str | None = None
    interprete_principal: str | None = None
    interpretes_invitados: str | None = None
    interprete_participante: str | None = None
    soporte_fisico: str | None = None
    editora: str | None = None
    numero_catalogo: str | None = None
    ciudad_edicion: str | None = None
    pais_edicion: str | None = None
    anio: str | None = None
    pistas: str | None = None
    observaciones: str | None = None
    version: int = 0


def fonograma_to_out(f: Fonograma) -> FonogramaOut:
    return FonogramaOut.model_validate(f)


class FonogramaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clave_fonograma: ClaveFonograma
    titulo: StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    subtitulo: str | None = Field(default=None, max_length=500)
    interprete_principal: str | None = Field(default=None, max_length=500)
    interpretes_invitados: str | None = Field(default=None, max_length=500)
    interprete_participante: str | None = Field(default=None, max_length=500)
    soporte_fisico: str | None = Field(default=None, max_length=200)
    editora: str | None = Field(default=None, max_length=200)
    numero_catalogo: str | None = Field(default=None, max_length=100)
    ciudad_edicion: str | None = Field(default=None, max_length=200)
    pais_edicion: str | None = Field(default=None, max_length=100)
    anio: str | None = Field(default=None, max_length=20)
    pistas: str | None = Field(default=None, max_length=2000)
    observaciones: str | None = Field(default=None, max_length=2000)


class SongOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fonograma_id: int
    title: str
    filename: str | None = None
    lyrics: str | None = None
    clasificacion: str | None = None
    tema: str | None = None
    autor: str | None = None
    compositor: str | None = None
    duracion: str | None = None
    personajes: str | None = None
    created_at: datetime
    version: int = 0


def song_to_out(s: Song) -> SongOut:
    return SongOut.model_validate(s)


class SongUpdate(BaseModel):
    """Admin-only song update. We persist title + lyrics per the Go
    AdminUpdateSong; other fields are surfaced but ignored. The
    backend is the source of truth for which columns get written.
    """
    model_config = ConfigDict(extra="forbid")

    title: StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    lyrics: str | None = Field(default=None, max_length=50_000)
    autor: str | None = Field(default=None, max_length=200)
    compositor: str | None = Field(default=None, max_length=200)
    duracion: str | None = Field(default=None, max_length=20)
    clasificacion: str | None = Field(default=None, max_length=100)
    tema: str | None = Field(default=None, max_length=200)


class SongCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fonograma_id: ClaveFonograma
    title: StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
    lyrics: str | None = Field(default=None, max_length=50_000)
    autor: str | None = Field(default=None, max_length=200)
    compositor: str | None = Field(default=None, max_length=200)
    duracion: str | None = Field(default=None, max_length=20)
    clasificacion: str | None = Field(default=None, max_length=100)
    tema: str | None = Field(default=None, max_length=200)


__all__ = [
    "FonogramaCreate",
    "FonogramaOut",
    "SongCreate",
    "SongOut",
    "SongUpdate",
    "fonograma_to_out",
    "song_to_out",
]
