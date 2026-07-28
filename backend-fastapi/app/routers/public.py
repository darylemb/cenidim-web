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

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import Integer, case, func, select

from app.deps import DbDep
from app.models.fonograma import Fonograma
from app.models.song import Song
from app.models.song_stats import SongStats
from app.models.theme_normalization import canonical_tema
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
    parse_int_or_none,
)

router = APIRouter(prefix="/api", tags=["public"])


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v for v in value.split(",") if v]


def _norm_themes(values: list[str]) -> list[str]:
    return [c for c in (canonical_tema(v) for v in values) if c]


# ---------------------------------------------------------------------------
# /api/search
# ---------------------------------------------------------------------------


@router.get("/search", response_model=dict)
async def search_songs(
    db: DbDep,
    q: Annotated[str, Query(max_length=200, alias="query", description="Search query (alias `query` for the Go frontend)")] = "",
    field: Annotated[str, Query(pattern="^(all|title|album|lyrics)$")] = "all",
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    order_by: Annotated[str, Query(pattern="^(id|clave|title|album|year|filename|clasificacion)$")] = "id",
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

    stmt = select(Song, Fonograma).join(
        Fonograma, Song.fonograma_id == Fonograma.clave_fonograma
    )

    if q:
        like = f"%{q}%"
        if field == "all":
            stmt = stmt.where(
                Song.title.like(like)
                | Fonograma.titulo.like(like)
                | Song.lyrics.like(like)
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

    canonical_themes = _norm_themes(_split_csv(tema))
    if canonical_themes:
        # canonical_tema strips whitespace from each slash segment, so
        # the SQL filter must mirror that with ``replace`` (not just
        # ``trim``) to match ``Vida/ muerte`` against ``Vida/Muerte``.
        normalised = [t.replace(" ", "").lower() for t in canonical_themes]
        stmt = stmt.where(
            func.replace(func.lower(func.trim(Song.tema)), " ", "").in_(normalised)
        )

    clases = _split_csv(clasificacion)
    if clases:
        stmt = stmt.where(Song.clasificacion.in_(clases))

    # Total count.
    count_q = select(func.count()).select_from(Song).join(
        Fonograma, Song.fonograma_id == Fonograma.clave_fonograma
    )
    if q:
        like = f"%{q}%"
        if field == "all":
            count_q = count_q.where(
                Song.title.like(like)
                | Fonograma.titulo.like(like)
                | Song.lyrics.like(like)
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
    if canonical_themes:
        count_q = count_q.where(
            func.replace(func.lower(func.trim(Song.tema)), " ", "").in_(
                [t.replace(" ", "").lower() for t in canonical_themes]
            )
        )
    if clases:
        count_q = count_q.where(Song.clasificacion.in_(clases))

    total = (await db.execute(count_q)).scalar_one()

    # Sort field map. NULL / empty strings sort last regardless of direction.
    sort_field = {
        "id": Song.id,
        "title": Song.title,
        "album": Fonograma.titulo,
        "year": Fonograma.anio,
        "filename": Song.filename,
        "clasificacion": Song.clasificacion,
        "clave": Fonograma.clave_fonograma,
    }[order_by]
    if order_by == "year":
        # ``anio`` is TEXT; cast for sort so '10' < '2' numeric.
        sort_field_cast = func.cast(Fonograma.anio, Integer)
        is_null = case(
            (Fonograma.anio.is_(None), 1),
            (Fonograma.anio == "", 1),
            (Fonograma.anio == "s/d", 1),
            else_=0,
        )
        sort_col = (
            sort_field_cast.asc() if order_dir == "asc" else sort_field_cast.desc()
        )
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
    song = (
        await db.execute(select(Song).where(Song.id == song_id))
    ).scalar_one_or_none()
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


@router.get("/timeline", response_model=TimelineData)
async def get_timeline(
    db: DbDep,
    query: Annotated[str, Query(max_length=500)] = "",
    limit: Annotated[int, Query(ge=1, le=5000)] = 5000,
) -> TimelineData:
    """All years present in the catalog + per-year song lists.

    The ``s/d`` bucket (no year) is omitted to keep the response
    compact; the dashboard surfaces it via a separate badge.
    """
    year_from, year_to = _parse_year_filter(query)

    stmt = select(Song, Fonograma, Fonograma.anio).join(
        Fonograma, Song.fonograma_id == Fonograma.clave_fonograma
    )
    if year_from is not None:
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) >= year_from)
    if year_to is not None:
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) <= year_to)
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
    stmt = (
        stmt.order_by(is_blank_year.asc(), func.cast(Fonograma.anio, Integer).asc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()

    timeline: dict[str, list[dict]] = {}
    for song, fonograma, year in rows:
        key = year or "s/d"
        timeline.setdefault(key, []).append(song_to_out(song, fonograma).model_dump())

    years_sorted = sorted(
        (y for y in timeline.keys() if y != "s/d"),
        key=lambda y: (int(y) if y.isdigit() else 9999),
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


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: DbDep,
    query: Annotated[str, Query(max_length=500)] = "",
) -> StatsResponse:
    """Aggregate metrics for the dashboard with the same shared
    filter logic as /api/search. Theme/classification are normalized
    via ``canonical_tema``.
    """
    year_from, _ = _parse_year_filter(query)

    base_count = select(func.count()).select_from(Song).join(
        Fonograma, Song.fonograma_id == Fonograma.clave_fonograma
    )
    if year_from is not None:
        base_count = base_count.where(
            func.cast(Fonograma.anio, Integer) >= year_from
        )
    total_songs = (await db.execute(base_count)).scalar_one()

    # Year buckets.
    year_stmt = (
        select(
            func.coalesce(Fonograma.anio, "Unknown").label("y"),
            func.count().label("n"),
        )
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    if year_from is not None:
        year_stmt = year_stmt.where(
            func.cast(Fonograma.anio, Integer) >= year_from
        )
    year_stmt = year_stmt.group_by(Fonograma.anio)
    songs_by_year = {row.y: row.n for row in (await db.execute(year_stmt)).all()}

    # Classification buckets (null -> 'ESPAÑOL_ESTANDAR').
    clas_stmt = (
        select(
            func.coalesce(Song.clasificacion, "ESPAÑOL_ESTANDAR").label("c"),
            func.count().label("n"),
        )
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    if year_from is not None:
        clas_stmt = clas_stmt.where(
            func.cast(Fonograma.anio, Integer) >= year_from
        )
    clas_stmt = clas_stmt.group_by(Song.clasificacion)
    songs_by_clas = {row.c: row.n for row in (await db.execute(clas_stmt)).all()}

    # Theme buckets (canonicalized).
    theme_stmt = (
        select(Song.tema, func.count().label("n"))
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
        .where(Song.tema.is_not(None), Song.tema != "")
    )
    if year_from is not None:
        theme_stmt = theme_stmt.where(
            func.cast(Fonograma.anio, Integer) >= year_from
        )
    theme_stmt = theme_stmt.group_by(Song.tema).order_by(func.count().desc())
    songs_by_theme: dict[str, int] = {}
    for theme, count in (await db.execute(theme_stmt)).all():
        c = canonical_tema(theme)
        if c:
            songs_by_theme[c] = songs_by_theme.get(c, 0) + count

    # Songs added in the last 30 days (compared to "now" in UTC).
    cutoff = func.datetime("now", "-30 days")
    recently_stmt = (
        select(func.count())
        .select_from(Song)
        .where(Song.created_at > cutoff)
    )
    recently_added = (await db.execute(recently_stmt)).scalar_one()

    # Distinct albums referenced by songs.
    albums_stmt = select(func.count(func.distinct(Song.fonograma_id))).select_from(
        Song
    )
    if year_from is not None:
        albums_stmt = albums_stmt.join(
            Fonograma, Song.fonograma_id == Fonograma.clave_fonograma
        ).where(func.cast(Fonograma.anio, Integer) >= year_from)
    total_albums = (await db.execute(albums_stmt)).scalar_one() or 0

    # Lyrics length averages.
    lyrics_stmt = select(Song.lyrics).select_from(Song)
    if year_from is not None:
        lyrics_stmt = lyrics_stmt.join(
            Fonograma, Song.fonograma_id == Fonograma.clave_fonograma
        ).where(func.cast(Fonograma.anio, Integer) >= year_from)
    lyrics_rows = (await db.execute(lyrics_stmt)).all()
    lyrics_lens = [len(r[0]) for r in lyrics_rows if r[0]]
    songs_with_lyrics = sum(1 for L in lyrics_lens if L > 0)
    avg_lyrics = (sum(lyrics_lens) / len(lyrics_lens)) if lyrics_lens else 0.0

    # Top albums (by track count).
    top_stmt = (
        select(
            Fonograma.titulo,
            Fonograma.anio,
            func.count().label("n"),
        )
        .select_from(Song)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    if year_from is not None:
        top_stmt = top_stmt.where(
            func.cast(Fonograma.anio, Integer) >= year_from
        )
    top_stmt = top_stmt.group_by(Fonograma.clave_fonograma).order_by(
        func.count().desc()
    ).limit(10)
    top_albums = [
        AlbumCount(album=row.titulo, year=row.anio, count=row.n)
        for row in (await db.execute(top_stmt)).all()
    ]

    # OOV / indigena buckets from song_stats.
    oov_rows = (await db.execute(select(SongStats.pct_oov))).all()
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
    indigena_rows = (await db.execute(select(SongStats.contiene_indigena))).all()
    by_indigena = {"CON_INDIGENA": 0, "SIN_INDIGENA": 0}
    for (flag,) in indigena_rows:
        if flag:
            by_indigena["CON_INDIGENA"] += 1
        else:
            by_indigena["SIN_INDIGENA"] += 1

    sin_anio = (
        await db.execute(
            select(func.count())
            .select_from(Song)
            .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
            .where(
                Fonograma.anio.is_(None)
                | (Fonograma.anio == "")
                | (Fonograma.anio == "s/d")
            )
        )
    ).scalar_one()

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


SPANISH_STOPWORDS = frozenset(
    word.lower()
    for word in (
        "el la los las un una unos unas de del al en a ante bajo con contra "
        "desde durante entre hacia hasta para por sin sobre tras y o u e que se "
        "es su sus lo le mi ti me te nos les este esta estos estas ese esa "
        "esos esas muy mucho mucha muchos muchas como cómo más menos ya yo "
        "tú él ella ellos ellas sí porque porque sí no sí ni también"
    ).split()
)

_MAX_WORDS = 8_000
_TOKEN_RE = re.compile(r"[\wáéíóúñüÁÉÍÓÚÑÜ]+", re.UNICODE)


def _extract_words(lyrics: str) -> list[str]:
    """Yield alphabetic tokens from a lyrics string (lower-cased)."""
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(lyrics or "")][:_MAX_WORDS]


@router.get("/word-cloud", response_model=WordCloudResponse)
async def get_word_cloud(
    db: DbDep,
    query: Annotated[str, Query(max_length=500)] = "",
) -> WordCloudResponse:
    """Top 500 most-frequent non-stop-word tokens across the catalog.

    Theme/year filters reuse the same parser as /api/search and /api/stats.
    """
    year_from, _ = _parse_year_filter(query)

    stmt = select(Song.lyrics).join(
        Fonograma, Song.fonograma_id == Fonograma.clave_fonograma
    )
    if year_from is not None:
        stmt = stmt.where(func.cast(Fonograma.anio, Integer) >= year_from)
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

    top = counter.most_common(500)
    max_c = top[0][1] if top else 1
    words = [
        WordFreq(text=t, size=10 + (c * 90 // max_c)) for t, c in top
    ]
    return WordCloudResponse(
        words=words,
        totalWords=total,
        excludedStopWords=excluded,
    )


__all__ = ["router"]
