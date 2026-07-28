"""Fonograma + Song Pydantic v2 schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.fonograma import Fonograma
from app.models.song import Song

ClaveFonograma = Annotated[int, Field(ge=1)]
SongId = Annotated[int, Field(ge=1)]

# String field with ``strip_whitespace`` + bounded length. Pydantic v2
# requires ``Annotated[str, StringConstraints(...)]`` - a bare
# ``StringConstraints(...)`` annotation is invalid (it isn't a class
# and has no ``__mro__``).
TituloStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]


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
    titulo: TituloStr
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
    """One row in the public catalog + admin song endpoints.

    Flat shape: every fonograma field the UI needs (album title,
    subtítulo, intérpretes, año, editora, …) is exposed at the
    top level so the frontend can render a single ``Song`` object
    without an extra fetch. The JOIN against ``fonogramas`` lives
    in the public/admin routers.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    fonograma_id: int

    # Song fields
    title: str
    filename: str | None = None
    lyrics: str | None = None
    clasificacion: str | None = None
    tema: str | None = None
    autor: str | None = None
    compositor: str | None = None
    duracion: str | None = None
    personajes: str | None = None

    # Fonograma fields (joined) — present for admin + public catalog
    album: str | None = None
    subtitulo: str | None = None
    interprete_principal: str | None = None
    interpretes_invitados: str | None = None
    interprete_participante: str | None = None
    soporte_fisico: str | None = None
    editora: str | None = None
    numero_catalogo: str | None = None
    ciudad_edicion: str | None = None
    pais_edicion: str | None = None
    year: str | None = None
    pistas: str | None = None
    observaciones: str | None = None

    created_at: datetime
    version: int = 0


def song_to_out(s: Song, fonograma: Fonograma | None = None) -> SongOut:
    """Render a Song row for the API.

    Pass the joined ``Fonograma`` (if the calling query did the JOIN)
    so the response can expose ``album``, ``year``, ``subtitulo``, …
    as flat top-level fields. When ``fonograma`` is omitted, those
    fields stay ``None`` — useful for the single-song endpoint which
    only knows the ``Song.id``.
    """
    payload = SongOut.model_validate(s).model_dump()
    if fonograma is not None:
        for f in (
            "album",
            "subtitulo",
            "interprete_principal",
            "interpretes_invitados",
            "interprete_participante",
            "soporte_fisico",
            "editora",
            "numero_catalogo",
            "ciudad_edicion",
            "pais_edicion",
            "year",
            "pistas",
            "observaciones",
        ):
            payload[f] = getattr(fonograma, f, None) or (
                fonograma.titulo if f == "album" else None
            )
        # ``album`` mirrors ``fonograma.titulo`` so the frontend's
        # ``Song.album`` field is non-null even when the column is.
        if payload["album"] is None:
            payload["album"] = fonograma.titulo
    return SongOut.model_validate(payload)


class SongUpdate(BaseModel):
    """Admin-only song update. We persist title + lyrics per the Go
    AdminUpdateSong; other fields are surfaced but ignored. The
    backend is the source of truth for which columns get written.
    """
    model_config = ConfigDict(extra="forbid")

    title: TituloStr
    lyrics: str | None = Field(default=None, max_length=50_000)
    autor: str | None = Field(default=None, max_length=200)
    compositor: str | None = Field(default=None, max_length=200)
    duracion: str | None = Field(default=None, max_length=20)
    clasificacion: str | None = Field(default=None, max_length=100)
    tema: str | None = Field(default=None, max_length=200)


class SongUpdateIn(BaseModel):
    """Request body for ``PUT /api/admin/songs/{id}``.

    Only the editable fields are exposed; the existing ``id`` /
    ``fonograma_id`` / ``created_at`` are read from the database.
    Mirrors the Go PUT semantics: only non-empty fields are
    persisted, matching its gorm.UpdateColumns-on-non-empty contract.
    """
    model_config = ConfigDict(extra="forbid")

    title: TituloStr | None = None
    lyrics: str | None = Field(default=None, max_length=50_000)


class SongCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fonograma_id: ClaveFonograma
    title: TituloStr
    lyrics: str | None = Field(default=None, max_length=50_000)
    autor: str | None = Field(default=None, max_length=200)
    compositor: str | None = Field(default=None, max_length=200)
    duracion: str | None = Field(default=None, max_length=20)
    clasificacion: str | None = Field(default=None, max_length=100)
    tema: str | None = Field(default=None, max_length=200)


class SongCreateIn(BaseModel):
    """Request body for ``POST /api/admin/songs``.

    Only the create-time fields are required; the ``id`` and the
    timestamp columns come from the database.
    """
    model_config = ConfigDict(extra="forbid")

    fonograma_id: ClaveFonograma
    title: TituloStr
    lyrics: str | None = Field(default=None, max_length=50_000)


__all__ = [
    "FonogramaCreate",
    "FonogramaOut",
    "SongCreate",
    "SongCreateIn",
    "SongOut",
    "SongUpdate",
    "SongUpdateIn",
    "fonograma_to_out",
    "song_to_out",
]
