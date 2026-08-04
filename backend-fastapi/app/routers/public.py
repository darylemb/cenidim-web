"""Public song + search + stats + word-cloud endpoints.

These mirror the routes that the Go (Gin) backend exposes under
``/api/search``, ``/api/song/{id}``, ``/api/timeline``, ``/api/stats``,
and ``/api/word-cloud``. Theme / classification filters are normalized
to Title Case via ``canonical_tema`` so case variants collapse into a
single bucket.

Phase 2: the search and timeline paths use SQLAlchemy 2.0 ORM
constructs rather than raw SQL strings, which lets the test suite
exercise them without the SQLAlchemy 2.0 ``text()`` requirement.
The stats and word-cloud routes still use text() because they
aggregate via SQL features (GROUP BY tema, etc.) that would be
verbose to express in ORM; those paths are covered by the dedicated
test suite in tests/api/test_public_router.py.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import Integer, case, func, or_, select

from app.deps import DbDep
from app.models.fonograma import Fonograma
from app.models.song import Song
from app.models.song_stats import SongStats
from app.models.theme_normalization import TEMA_TYPO_MAP, canonical_tema
from app.schemas.song import SongOut, song_to_out
from app.schemas.stats import (
    AlbumCount,
    StatsResponse,
    TimelineData,
    WordCloudResponse,
    WordFreq,
)
from app.services.filters import (
    AlbumQ,
    ClasificacionList,
    TemaList,
    YearFromQ,
    YearToQ,
    normalize_year,
    parse_int_or_none,
)

router = APIRouter(prefix="/api", tags=["public"])


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v for v in value.split(",") if v]


def _norm_themes(values: list[str]) -> list[str]:
    return [c for c in (canonical_tema(v) for v in values) if c]


def _tema_filter_variants(canonical: str) -> list[str]:
    """All raw spellings that should match a canonical theme.

    For each slash segment we consider the canonical spelling plus any
    typo variant (reverse of ``TEMA_TYPO_MAP``). The cartesian product
    covers mixed forms such as ``Solidarida/Individualismo`` when the
    operator picks the canonical ``Solidaridad/Individualismo`` chip.
    """
    import itertools

    segments = canonical.split("/")
    per_seg: list[list[str]] = []
    for seg in segments:
        base = seg.replace(" ", "").lower()
        variants = {base}
        for typo, fixed in TEMA_TYPO_MAP.items():
            if base == fixed:
                variants.add(typo)
            elif base == typo:
                variants.add(fixed)
        per_seg.append(sorted(variants))
    combos = list(itertools.product(*per_seg))
    return ["/".join(c) for c in combos]


# Sentinel used by the dashboard for "songs with no declared theme".
# The chip label is "Sin tema"; the store sends this literal value.
THEME_NONE_SENTINEL = "__none__"


def _tema_filter_clause(temas: list[str]):
    """SQLAlchemy WHERE clause that matches any of the given themes.

    The input list may contain raw or canonical spellings; the clause
    normalises each one and expands typo variants so a canonical chip
    still matches rows stored under a typo (``Solidaridad`` vs
    ``Solidarida``). The ``__none__`` sentinel matches rows whose tema
    is NULL/empty (the dashboard's "Sin tema" chip). Returns ``None``
    when there is nothing to filter.
    """
    named = [t for t in temas if t != THEME_NONE_SENTINEL]
    has_none = THEME_NONE_SENTINEL in temas

    clauses = []
    if named:
        normalised = [v for ct in _norm_themes(named) for v in _tema_filter_variants(ct)]
        if normalised:
            clauses.append(
                func.replace(func.lower(func.trim(Song.tema)), " ", "").in_(normalised)
            )
    if has_none:
        clauses.append(Song.tema.is_(None) | (Song.tema == ""))

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return or_(*clauses)


# ---------------------------------------------------------------------------
# /api/search
# ---------------------------------------------------------------------------


@router.get("/search", response_model=dict)
async def search_songs(
    db: DbDep,
    q: Annotated[
        str,
        Query(
            max_length=200,
            alias="query",
            description="Search query (alias `query` for the Go frontend)",
        ),
    ] = "",
    field: Annotated[str, Query(pattern="^(all|title|album|lyrics)$")] = "all",
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    order_by: Annotated[
        str,
        Query(
            pattern="^(id|clave|title|album|year|filename|clasificacion|subtitulo|interprete_principal|interpretes_invitados|interprete_participante|soporte_fisico|editora|numero_catalogo|ciudad_edicion|pais_edicion|pistas|observaciones|tema)$"
        ),
    ] = "id",
    order_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
    tema: TemaList = None,
    year_from: YearFromQ = None,
    year_to: YearToQ = None,
    clasificacion: ClasificacionList = None,
    album: AlbumQ = None,
) -> dict:
    """Search songs with optional filters.

    Theme/classification are exact-match after lowercasing so case
    variants collapse into a single bucket. Year range is bounded
    by ``year_from <= year_to``; the helper raises 400 if inverted.

    The ``q`` parameter is also exposed as ``query`` so the existing
    Vue dashboard (which sends ``?query=...``) keeps working
    without a frontend change.
    """
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(status_code=400, detail="year_from must be <= year_to")

    stmt = select(Song, Fonograma).join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)

    if q:
        like = f"%{q}%"
        if field == "all":
            stmt = stmt.where(
                Song.title.like(like) | Fonograma.titulo.like(like) | Song.lyrics.like(like)
            )
        elif field == "title":
            stmt = stmt.where(Song.title.like(like))
        elif field == "album":
            stmt = stmt.where(Fonograma.titulo.like(like))
        else:  # lyrics
            stmt = stmt.where(Song.lyrics.like(like))

    if year_from is not None:
        # ``anio`` is stored as TEXT; cast to int for range comparisons.
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) >= year_from)
    if year_to is not None:
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) <= year_to)
    if album:
        stmt = stmt.where(Fonograma.titulo == album)

    theme_filter = _tema_filter_clause(_split_csv(tema))
    if theme_filter is not None:
        stmt = stmt.where(theme_filter)

    clases = _split_csv(clasificacion)
    if clases:
        stmt = stmt.where(Song.clasificacion.in_(clases))

    # Total count.
    count_q = (
        select(func.count())
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    if q:
        like = f"%{q}%"
        if field == "all":
            count_q = count_q.where(
                Song.title.like(like) | Fonograma.titulo.like(like) | Song.lyrics.like(like)
            )
        elif field == "title":
            count_q = count_q.where(Song.title.like(like))
        elif field == "album":
            count_q = count_q.where(Fonograma.titulo.like(like))
        else:
            count_q = count_q.where(Song.lyrics.like(like))
    if year_from is not None:
        count_q = count_q.where(func.cast(Fonograma.anio, Integer) >= year_from)
    if year_to is not None:
        count_q = count_q.where(func.cast(Fonograma.anio, Integer) <= year_to)
    if album:
        count_q = count_q.where(Fonograma.titulo == album)
    if theme_filter is not None:
        count_q = count_q.where(theme_filter)
    if clases:
        count_q = count_q.where(Song.clasificacion.in_(clases))

    total = (await db.execute(count_q)).scalar_one()

    # Sort field map. NULL / empty strings sort last regardless of direction.
    # Fonograma-only columns (subtitulo, interprete_*, editora, …) sort
    # on the joined row so the catalog can order by every visible column
    # (review request 03/ago/2026).
    sort_field = {
        "id": Song.id,
        "title": Song.title,
        "album": Fonograma.titulo,
        "year": Fonograma.anio,
        "filename": Song.filename,
        "clasificacion": Song.clasificacion,
        "clave": Fonograma.clave_fonograma,
        "subtitulo": Fonograma.subtitulo,
        "interprete_principal": Fonograma.interprete_principal,
        "interpretes_invitados": Fonograma.interpretes_invitados,
        "interprete_participante": Fonograma.interprete_participante,
        "soporte_fisico": Fonograma.soporte_fisico,
        "editora": Fonograma.editora,
        "numero_catalogo": Fonograma.numero_catalogo,
        "ciudad_edicion": Fonograma.ciudad_edicion,
        "pais_edicion": Fonograma.pais_edicion,
        "pistas": Fonograma.pistas,
        "observaciones": Fonograma.observaciones,
        "tema": Song.tema,
    }[order_by]
    if order_by == "year":
        # ``anio`` is TEXT and has dirty values like ``[1982]`` or
        # ``1965 (disco 1)...`` that ``CAST(... AS INTEGER)`` would
        # collapse to 0. The ``normalize_year`` SQLite UDF registered
        # in app/db/session.py mirrors the Python helper so SQL
        # ORDER BY and the JSON response agree (``[1982]`` sorts next
        # to ``1982``, not before every real year).
        # The UDF returns 0 for null/empty/s-d, but we want those rows
        # last regardless of direction. The is_null case (0/1) is
        # added to ORDER BY so they sort at the end; the year sort key
        # is added on top.
        sort_field_cast = func.normalize_year(Fonograma.anio)
        is_null = case(
            (Fonograma.anio.is_(None), 1),
            (Fonograma.anio == "", 1),
            (Fonograma.anio == "s/d", 1),
            else_=0,
        )
        if order_dir == "asc":
            sort_col = sort_field_cast.asc()
        else:
            sort_col = sort_field_cast.desc()
    else:
        is_null = case(
            (sort_field.is_(None), 1),
            (sort_field == "", 1),
            else_=0,
        )
        sort_col = sort_field.asc() if order_dir == "asc" else sort_field.desc()
    stmt = stmt.order_by(is_null, sort_col).limit(limit).offset((page - 1) * limit)

    rows = (await db.execute(stmt)).all()
    songs: list[SongOut] = []
    for song, fonograma in rows:
        songs.append(song_to_out(song, fonograma))
    return {"results": [s.model_dump() for s in songs], "total": total}


# ---------------------------------------------------------------------------
# /api/song/{id}
# ---------------------------------------------------------------------------


@router.get("/song/{song_id}", response_model=SongOut)
async def get_song_detail(song_id: int, db: DbDep) -> SongOut:
    song = (await db.execute(select(Song).where(Song.id == song_id))).scalar_one_or_none()
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return song_to_out(song)


# ---------------------------------------------------------------------------
# /api/timeline
# ---------------------------------------------------------------------------


def _parse_year_filter(query: str) -> tuple[int | None, int | None]:
    """Pull year_from / year_to from the shared ``query`` string."""
    year_from = None
    year_to = None
    for p in query.split("&"):
        if p.startswith("year_from="):
            year_from = parse_int_or_none(p.split("=", 1)[1])
        elif p.startswith("year_to="):
            year_to = parse_int_or_none(p.split("=", 1)[1])
    return year_from, year_to


def _get_request(request: Request) -> Request:
    return request


@router.get("/timeline", response_model=TimelineData)
async def get_timeline(
    db: DbDep = ...,
    request: Request = Depends(_get_request),
    query: str = Query("", max_length=500),
    limit: int = Query(5000, ge=1, le=5000),
    year_from: YearFromQ = None,
    year_to: YearToQ = None,
    clasificacion: ClasificacionList = None,
    tema: TemaList = None,
    album: AlbumQ = None,
) -> TimelineData:
    """All years present in the catalog + per-year song lists.

    The ``s/d`` bucket (no year) is omitted to keep the response
    compact; the dashboard surfaces it via a separate badge.
    """
    # Back-compat: pull year/clas/theme tokens from the shared
    # ``query`` blob when not supplied as explicit params.
    legacy_year_from, legacy_year_to = _parse_year_filter(query)
    year_from = year_from if year_from is not None else legacy_year_from
    year_to = year_to if year_to is not None else legacy_year_to
    if not tema:
        tema = _alias_theme_from_request(request)

    stmt = select(Song, Fonograma, Fonograma.anio).join(
        Fonograma, Song.fonograma_id == Fonograma.clave_fonograma
    )
    if year_from is not None:
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) >= year_from)
    if year_to is not None:
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) <= year_to)
    if album:
        stmt = stmt.where(Fonograma.titulo == album)
    if clasificacion:
        _clases = [c for c in clasificacion.split(",") if c]
        if _clases:
            stmt = stmt.where(func.coalesce(Song.clasificacion, "ESPAÑOL_ESTANDAR").in_(_clases))
    theme_filter = _tema_filter_clause([t for t in (tema or "").split(",") if t])
    if theme_filter is not None:
        stmt = stmt.where(theme_filter)
    # Sort "s/d" / empty / NULL years AFTER the real years. SQLite's
    # ``CAST(... AS INTEGER)`` maps all of them to 0, which would
    # otherwise sort them first and crowd the ``limit`` window with
    # the no-year bucket, hiding the real decades entirely.
    is_blank_year = case(
        (Fonograma.anio.is_(None), 1),
        (Fonograma.anio == "", 1),
        (Fonograma.anio == "s/d", 1),
        else_=0,
    )
    stmt = stmt.order_by(is_blank_year.asc(), func.cast(Fonograma.anio, Integer).asc()).limit(limit)
    rows = (await db.execute(stmt)).all()

    timeline: dict[str, list[dict]] = {}
    for song, fonograma, year in rows:
        # Normalize the dirty ``anio`` column so "[1982]" / multi-year
        # strings don't leak into the timeline keys. ``s/d`` /
        # empty / NULL collapse to the "s/d" bucket.
        key = normalize_year(year) or "s/d"
        timeline.setdefault(key, []).append(song_to_out(song, fonograma).model_dump())

    years_sorted = sorted(
        (y for y in timeline.keys() if y != "s/d"),
        # All keys here are already 4-digit strings.
        key=lambda y: int(y),
    )
    if "s/d" in timeline:
        years_sorted.append("s/d")

    total = sum(len(v) for v in timeline.values())
    return TimelineData(
        years=years_sorted,
        timeline=timeline,
        total=total,
        truncated=total > limit,
    )


# ---------------------------------------------------------------------------
# /api/stats
# ---------------------------------------------------------------------------


def _alias_theme_from_request(request: Request) -> str | None:
    """Pull ``theme=`` (English) as an alias for ``?tema=`` (Spanish).

    The Pinia filter store in the Vue dashboard composes the
    dashboard query as ``?theme=Cuentos`` for backward-compat with
    the Go (Gin) backend. The original FastAPI routes accept only
    ``?tema=``. Accept both for one release so the frontend has
    time to standardise on one of them.
    """
    for tok in request.url.query.split("&"):
        if tok.startswith("theme="):
            return tok.split("=", 1)[1]
    return None


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    request: Request = Depends(_get_request),
    db: DbDep = ...,
    query: str = Query("", max_length=500),
    year_from: YearFromQ = None,
    year_to: YearToQ = None,
    clasificacion: ClasificacionList = None,
    tema: TemaList = None,
    album: AlbumQ = None,
) -> StatsResponse:
    """Aggregate metrics for the dashboard with the same shared
    filter logic as /api/search. Theme/classification are normalized
    via ``canonical_tema``. ``year_from`` and ``year_to`` are
    accepted as both query params (``?year_from=1970``) and as
    tokens embedded in ``query`` (legacy Go-backend convention).
    """
    # Back-compat: pull year/clas/theme tokens from the shared
    # ``query`` blob when not supplied as explicit params.
    legacy_year_from, legacy_year_to = _parse_year_filter(query)
    year_from = year_from if year_from is not None else legacy_year_from
    year_to = year_to if year_to is not None else legacy_year_to

    # Accept ``?theme=`` as an alias for ``?tema=``.
    if not tema:
        tema = _alias_theme_from_request(request)

    # Reusable clause that joins fonograma + applies the year filter.
    # ``anio`` is TEXT; we CAST to Integer so the inequality uses
    # numeric ordering rather than lexicographic ('10' < '2').
    def _joined_base():
        s = select(Song).join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
        if year_from is not None:
            s = s.where(func.cast(Fonograma.anio, Integer) >= year_from)
        if year_to is not None:
            s = s.where(func.cast(Fonograma.anio, Integer) <= year_to)
        return s

    # Apply the same year + tema + clasification + album filters
    # to every bucket below. Tema is OR-ed (any match counts) and
    # canonicalized at the bottom of the response. ``album`` is
    # the FONOGRAMA.titulo (not the song's).
    #
    # ``clasificacion`` and ``tema`` arrive as comma-separated
    # strings per the ClasificacionList / TemaList filter types,
    # so we split on ``,`` before applying.
    _clases = [c for c in (clasificacion or "").split(",") if c]
    _temas = [t for t in (tema or "").split(",") if t]
    _theme_filter = _tema_filter_clause(_temas)

    def _apply_filters(stmt):
        if year_from is not None:
            stmt = stmt.where(func.cast(Fonograma.anio, Integer) >= year_from)
        if year_to is not None:
            stmt = stmt.where(func.cast(Fonograma.anio, Integer) <= year_to)
        if album:
            stmt = stmt.where(Fonograma.titulo == album)
        if _clases:
            stmt = stmt.where(func.coalesce(Song.clasificacion, "ESPAÑOL_ESTANDAR").in_(_clases))
        if _theme_filter is not None:
            stmt = stmt.where(_theme_filter)
        return stmt

    base_count = select(func.count()).select_from(_apply_filters(_joined_base()).subquery())
    total_songs = (await db.execute(base_count)).scalar_one()

    # Year buckets — group by normalized year so "[1982]" and
    # "s/d" don't leak into the chart.
    year_stmt = (
        select(
            Fonograma.anio.label("raw"),
            func.count().label("n"),
        )
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    year_stmt = _apply_filters(year_stmt)
    if year_from is not None:
        year_stmt = year_stmt.where(func.cast(Fonograma.anio, Integer) >= year_from)
    if year_to is not None:
        year_stmt = year_stmt.where(func.cast(Fonograma.anio, Integer) <= year_to)
    year_stmt = year_stmt.group_by(Fonograma.anio)
    songs_by_year: dict[str, int] = {}
    for row in (await db.execute(year_stmt)).all():
        ny = normalize_year(row.raw)
        if ny is None:
            continue  # s/d, empty, NULL — surfaced via songs_without_year
        songs_by_year[ny] = songs_by_year.get(ny, 0) + row.n

    # Classification buckets (null -> 'ESPAÑOL_ESTANDAR').
    clas_stmt = (
        select(
            func.coalesce(Song.clasificacion, "ESPAÑOL_ESTANDAR").label("c"),
            func.count().label("n"),
        )
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    clas_stmt = _apply_filters(clas_stmt)
    clas_stmt = clas_stmt.group_by(Song.clasificacion)
    songs_by_clas = {row.c: row.n for row in (await db.execute(clas_stmt)).all()}

    # Theme buckets (canonicalized).
    theme_stmt = (
        select(Song.tema, func.count().label("n"))
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
        .where(Song.tema.is_not(None), Song.tema != "")
    )
    theme_stmt = _apply_filters(theme_stmt)
    theme_stmt = theme_stmt.group_by(Song.tema).order_by(func.count().desc())
    songs_by_theme: dict[str, int] = {}
    for theme, count in (await db.execute(theme_stmt)).all():
        c = canonical_tema(theme)
        if c:
            songs_by_theme[c] = songs_by_theme.get(c, 0) + count

    # Songs added in the last 30 days (compared to "now" in UTC).
    cutoff = func.datetime("now", "-30 days")
    recently_stmt = select(func.count()).select_from(Song).where(Song.created_at > cutoff)
    recently_added = (await db.execute(recently_stmt)).scalar_one()

    # Distinct albums referenced by songs.
    albums_stmt = select(func.count(func.distinct(Song.fonograma_id))).select_from(Song)
    if any([year_from, year_to, album, clasificacion, tema]):
        albums_stmt = albums_stmt.join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    albums_stmt = _apply_filters(albums_stmt)
    total_albums = (await db.execute(albums_stmt)).scalar_one() or 0

    # Lyrics length averages.
    lyrics_stmt = select(Song.lyrics).select_from(Song)
    if any([year_from, year_to, album, clasificacion, tema]):
        lyrics_stmt = lyrics_stmt.join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    lyrics_stmt = _apply_filters(lyrics_stmt)
    lyrics_rows = (await db.execute(lyrics_stmt)).all()
    lyrics_lens = [len(r[0]) for r in lyrics_rows if r[0]]
    songs_with_lyrics = sum(1 for L in lyrics_lens if L > 0)
    avg_lyrics = (sum(lyrics_lens) / len(lyrics_lens)) if lyrics_lens else 0.0

    # Top albums (by track count) — uses normalized year too.
    top_stmt = (
        select(
            Fonograma.titulo,
            Fonograma.anio,
            func.count().label("n"),
        )
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    top_stmt = _apply_filters(top_stmt)
    top_stmt = top_stmt.group_by(Fonograma.clave_fonograma).order_by(func.count().desc()).limit(10)
    top_albums = [
        AlbumCount(
            album=row.titulo,
            year=normalize_year(row.anio) or "",
            count=row.n,
        )
        for row in (await db.execute(top_stmt)).all()
    ]

    # OOV / indigena buckets from song_stats — these don't have a
    # fonograma_id so the year filter needs a join.
    oov_stmt = (
        select(SongStats.pct_oov)
        .join(Song, SongStats.song_id == Song.id)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    oov_stmt = _apply_filters(oov_stmt)
    oov_rows = (await db.execute(oov_stmt)).all()
    by_oov = {"BAJA": 0, "MEDIA": 0, "ALTA": 0}
    for (pct,) in oov_rows:
        if pct is None:
            continue
        if pct < 5:
            by_oov["BAJA"] += 1
        elif pct < 18:
            by_oov["MEDIA"] += 1
        else:
            by_oov["ALTA"] += 1

    indigena_stmt = (
        select(SongStats.contiene_indigena)
        .join(Song, SongStats.song_id == Song.id)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    indigena_stmt = _apply_filters(indigena_stmt)
    indigena_rows = (await db.execute(indigena_stmt)).all()
    by_indigena = {"CON_INDIGENA": 0, "SIN_INDIGENA": 0}
    for (flag,) in indigena_rows:
        if flag:
            by_indigena["CON_INDIGENA"] += 1
        else:
            by_indigena["SIN_INDIGENA"] += 1

    # Songs whose fonograma has no clean year ("s/d" / empty / NULL)
    # — always exposed so the dashboard can render a "Sin año"
    # KPI alongside the filtered set. We do NOT apply the year
    # range filter here because "no year" is conceptually disjoint
    # from "year between X and Y".
    sin_anio = (
        await db.execute(
            select(func.count())
            .select_from(Song)
            .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
            .where(Fonograma.anio.is_(None) | (Fonograma.anio == ""))
        )
    ).scalar_one() + sum(
        1
        for (v,) in (
            await db.execute(
                select(Fonograma.anio).join(Song, Song.fonograma_id == Fonograma.clave_fonograma)
            )
        ).all()
        if v == "s/d"
    )

    return StatsResponse(
        total_songs=total_songs,
        total_albums=total_albums,
        catalog_total=total_songs,
        recently_added=recently_added,
        songs_with_lyrics=songs_with_lyrics,
        avg_lyrics_length=avg_lyrics,
        songs_by_year=songs_by_year,
        songs_by_clasificacion=songs_by_clas,
        songs_by_theme=songs_by_theme,
        distinct_themes=len(songs_by_theme),
        top_albums=top_albums,
        songs_by_oov_level=by_oov,
        songs_by_indigena=by_indigena,
        songs_without_year=sin_anio,
    )


# ---------------------------------------------------------------------------
# /api/word-cloud
# ---------------------------------------------------------------------------


# IMPORTANT: every string ends with a trailing space (Python
# concatenates adjacent string literals without inserting a space —
# a space-free join would merge "del"+"a" into "dela" and silently
# drop both stop-words from the set).
SPANISH_STOPWORDS = frozenset(
    w.lower()
    for w in (
        # determinantes / artículos
        "el la los las un una unos unas lo al del "
        # preposiciones
        "a ante bajo con contra de desde durante en entre hacia hasta para "
        "por según sin sobre tras "
        # conjunciones
        "y o u e ni que aunque pero porque "
        # pronombres
        "se su sus le lo mi ti me te nos les este esta estos estas ese esa "
        "esos esas yo tú tu él ella ellos ellas usted ustedes mí sí "
        # adverbios / cuantificadores
        "muy mucho mucha muchos muchas poco poca pocos pocas más menos tan como "
        "cómo cuánto cuánta cuántos cuántas ya no si también cuando dónde donde "
        "quién qué "
        # verbos frecuentes (ser, estar, tener, ir, saber, dar, ver, hacer)
        "es ser era soy eres son somos estaba estaban estoy está están tiene "
        "tienen tener tengo hay había va ir voy vamos siendo sabe sabes saber "
        "doy da dio vi ver hago hace hacer "
        # misceláneos
        "todo toda todos todas bien ay aquí ahí allí"
    ).split()
)

_MAX_WORDS = 8_000
_TOKEN_RE = re.compile(r"[\wáéíóúñüÁÉÍÓÚÑÜ]+", re.UNICODE)

# Metadata marker lines that classify_songs strips from the stored
# lyrics but that ~8% of records still carry in the database. Skipping
# them here (instead of filtering the bare words) means the word cloud
# stays clean even before the data is re-processed, while real Spanish
# words like "tema" or "personajes" in an actual lyric are preserved.
_META_LINE_RE = re.compile(
    r"^\s*(?:dura|duración|duracion|tema|subtema|personajes|autor|compositor|comp)\s*:",
    re.IGNORECASE,
)


def _extract_words(lyrics: str) -> list[str]:
    """Yield alphabetic tokens from a lyrics string (lower-cased).

    Skips metadata marker lines (``Dura:``, ``Tema:``, ``Personajes:``,
    ``Autor:`` …), single-character tokens, and pure-numeric tokens so
    the cloud reflects the actual lyric vocabulary rather than headers,
    stray initials (``M.G.A.`` → ``m``, ``g``) or counts.
    """
    out: list[str] = []
    for line in (lyrics or "").splitlines():
        if _META_LINE_RE.match(line):
            continue
        for m in _TOKEN_RE.finditer(line):
            tok = m.group(0).lower()
            if len(tok) < 2 or tok.isdigit():
                continue
            out.append(tok)
            if len(out) >= _MAX_WORDS:
                return out
    return out


@router.get("/word-cloud", response_model=WordCloudResponse)
async def get_word_cloud(
    db: DbDep = ...,
    request: Request = Depends(_get_request),
    query: str = Query("", max_length=500),
    limit: int = Query(200, ge=1, le=500),
    year_from: YearFromQ = None,
    year_to: YearToQ = None,
    clasificacion: ClasificacionList = None,
    tema: TemaList = None,
    album: AlbumQ = None,
) -> WordCloudResponse:
    """Top ``limit`` most-frequent non-stop-word tokens across the catalog.

    Defaults to 200 words (the 500-word all-catalog view produced too
    much crowding — reviewer feedback 01/jul/2026). The dashboard can
    request more via ``?limit=500`` if needed. Theme / classification
    / album / year filters mirror the same filter pipeline as
    ``/api/search`` and ``/api/stats`` so the dashboard word cloud
    updates when the user narrows the year range or toggles a chip.
    """
    # Back-compat: pull year/clas/theme tokens from the shared
    # ``query`` blob when not supplied as explicit params.
    legacy_year_from, legacy_year_to = _parse_year_filter(query)
    year_from = year_from if year_from is not None else legacy_year_from
    year_to = year_to if year_to is not None else legacy_year_to
    if not tema:
        tema = _alias_theme_from_request(request)

    stmt = select(Song.lyrics).join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    if year_from is not None:
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) >= year_from)
    if year_to is not None:
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) <= year_to)
    if album:
        stmt = stmt.where(Fonograma.titulo == album)
    if clasificacion:
        _clases = [c for c in clasificacion.split(",") if c]
        if _clases:
            stmt = stmt.where(func.coalesce(Song.clasificacion, "ESPAÑOL_ESTANDAR").in_(_clases))
    theme_filter = _tema_filter_clause([t for t in (tema or "").split(",") if t])
    if theme_filter is not None:
        stmt = stmt.where(theme_filter)
    stmt = stmt.limit(_MAX_WORDS)
    rows = (await db.execute(stmt)).all()

    counter: Counter[str] = Counter()
    excluded = 0
    total = 0
    for (lyrics,) in rows:
        for w in _extract_words(lyrics or ""):
            total += 1
            if w in SPANISH_STOPWORDS:
                excluded += 1
                continue
            counter[w] += 1

    top = counter.most_common(limit)
    max_c = top[0][1] if top else 1
    words = [WordFreq(text=t, size=10 + (c * 90 // max_c)) for t, c in top]
    return WordCloudResponse(
        words=words,
        totalWords=total,
        excludedStopWords=excluded,
    )


__all__ = ["router"]
