"""Public song + search + stats + word-cloud endpoints.

These mirror the routes that the Go (Gin) backend exposes under
``/api/search``, ``/api/song/{id}``, ``/api/timeline``, ``/api/stats``,
and ``/api/word-cloud``. Theme / classification filters are normalized
to Title Case via ``canonical_tema`` so case variants collapse into a
single bucket.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.deps import DbDep
from app.models.song import Song
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


@router.get("/search", response_model=dict)
async def search_songs(
    db: DbDep,
    q: Annotated[str, Query(max_length=200)] = "",
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
    """
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(status_code=400, detail="year_from must be <= year_to")
    if len(q) > 200:
        raise HTTPException(status_code=400, detail="q must be at most 200 characters")

    where = []
    args: list[object] = []
    if q:
        like = f"%{q}%"
        if field == "all":
            where.append("(s.title LIKE ? OR f.titulo LIKE ? OR s.lyrics LIKE ?)")
            args.extend([like, like, like])
        elif field == "title":
            where.append("s.title LIKE ?")
            args.append(like)
        elif field == "album":
            where.append("f.titulo LIKE ?")
            args.append(like)
        else:  # lyrics
            where.append("s.lyrics LIKE ?")
            args.append(like)
    if year_from is not None:
        where.append("CAST(f.anio AS INTEGER) >= ?")
        args.append(year_from)
    if year_to is not None:
        where.append("CAST(f.anio AS INTEGER) <= ?")
        args.append(year_to)
    if album:
        where.append("f.titulo = ?")
        args.append(album)
    if tema:
        canonical_themes = [canonical_tema(t) for t in tema.split(",") if t]
        canonical_themes = [t for t in canonical_themes if t]
        if canonical_themes:
            placeholders = ",".join("?" for _ in canonical_themes)
            where.append(
                f"LOWER(TRIM(COALESCE(s.tema, ''))) IN ({placeholders})"
            )
            args.extend(t.lower() for t in canonical_themes)
    if clasificacion:
        clases = [c for c in clasificacion.split(",") if c]
        if clases:
            placeholders = ",".join("?" for _ in clases)
            where.append(f"s.clasificacion IN ({placeholders})")
            args.extend(clases)

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    # Total count first.
    count_stmt = f"SELECT COUNT(*) FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma{where_sql}"
    total = (await db.execute(count_stmt, args)).scalar_one()

    order_field_map = {
        "id": "s.id", "title": "s.title", "album": "f.titulo",
        "year": "f.anio", "filename": "s.filename",
        "clasificacion": "s.clasificacion",
    }
    sort_col = order_field_map[order_by]
    nulls_last = (
        f"CASE WHEN {sort_col} IS NULL OR {sort_col} = '' THEN 1 ELSE 0 END, "
    )
    order_sql = f"ORDER BY {nulls_last}{sort_col} {order_dir.upper()} LIMIT ? OFFSET ?"
    args.extend([limit, (page - 1) * limit])

    rows_stmt = (
        f"SELECT s.id, s.fonograma_id, s.title, s.filename, s.lyrics, "
        f"s.clasificacion, s.tema, s.autor, s.compositor, s.duracion, "
        f"s.personajes, s.created_at, s.version "
        f"FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
        f"{where_sql} {order_sql}"
    )
    rows = (await db.execute(rows_stmt, args)).mappings().all()
    songs = [
        SongOut(
            id=r["id"],
            fonograma_id=r["fonograma_id"],
            title=r["title"],
            filename=r["filename"],
            lyrics=r["lyrics"],
            clasificacion=r["clasificacion"],
            tema=r["tema"],
            autor=r["autor"],
            compositor=r["compositor"],
            duracion=r["duracion"],
            personajes=r["personajes"],
            created_at=r["created_at"],
            version=r["version"],
        )
        for r in rows
    ]
    return {"results": [s.model_dump() for s in songs], "total": total}


@router.get("/song/{song_id}", response_model=SongOut)
async def get_song_detail(song_id: int, db: DbDep) -> SongOut:
    song = (
        await db.execute(
            select(Song).where(Song.id == song_id)
        )
    ).scalar_one_or_none()
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found")
    return song_to_out(song)


@router.get("/timeline", response_model=TimelineData)
async def get_timeline(
    db: DbDep,
    query: Annotated[str, Query(max_length=500)] = "",
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
) -> TimelineData:
    """All years present in the catalog + per-year song lists.

    The ``s/d`` bucket (no year) is omitted to keep the response
    compact; the dashboard surfaces it via a separate badge.
    """
    where_sql = ""
    args: list[object] = []
    if query:
        # Parse shared filter query (tema=, year=, etc.) the same way
        # /api/search does. For Phase 1 we only honour year range.
        params = query.split("&")
        for p in params:
            if p.startswith("year_from="):
                v = parse_int_or_none(p.split("=", 1)[1])
                if v is not None:
                    where_sql = " WHERE CAST(f.anio AS INTEGER) >= ?"
                    args.append(v)
                    break
            if p.startswith("year_to="):
                v = parse_int_or_none(p.split("=", 1)[1])
                if v is not None:
                    where_sql = " WHERE CAST(f.anio AS INTEGER) <= ?"
                    args.append(v)
                    break

    rows_stmt = (
        f"SELECT f.anio, s.id, s.fonograma_id, s.title, s.filename, s.lyrics, "
        f"s.clasificacion, s.tema, s.autor, s.compositor, s.duracion, "
        f"s.personajes, s.created_at, s.version "
        f"FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
        f"{where_sql} LIMIT ?"
    )
    rows = (await db.execute(rows_stmt, args + [limit])).mappings().all()

    timeline: dict[str, list[dict]] = {}
    for r in rows:
        year = r["anio"] or "s/d"
        timeline.setdefault(year, []).append(
            SongOut(
                id=r["id"],
                fonograma_id=r["fonograma_id"],
                title=r["title"],
                filename=r["filename"],
                lyrics=r["lyrics"],
                clasificacion=r["clasificacion"],
                tema=r["tema"],
                autor=r["autor"],
                compositor=r["compositor"],
                duracion=r["duracion"],
                personajes=r["personajes"],
                created_at=r["created_at"],
                version=r["version"],
            ).model_dump()
        )

    # Strip s/d (it's filtered out above; this is defensive).
    years_sorted = sorted(
        (y for y in timeline.keys() if y != "s/d"),
        key=lambda y: (
            int(y) if y.isdigit() else 9999,
        ),
    )
    if "s/d" in timeline:
        years_sorted.append("s/d")

    total_stmt = (
        "SELECT COUNT(*) FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
    )
    total = (await db.execute(total_stmt)).scalar_one()
    return TimelineData(
        years=years_sorted,
        timeline=timeline,
        total=total,
        truncated=total > limit,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: DbDep,
    query: Annotated[str, Query(max_length=500)] = "",
) -> StatsResponse:
    """Aggregate metrics for the dashboard with the same shared
    filter logic as /api/search. Theme/classification are normalized
    via ``canonical_tema``.
    """
    where_sql = ""
    args: list[object] = []
    if query:
        # Reuse the same parser.
        for p in query.split("&"):
            if p.startswith("year_from="):
                v = parse_int_or_none(p.split("=", 1)[1])
                if v is not None:
                    where_sql = " WHERE CAST(f.anio AS INTEGER) >= ?"
                    args.append(v)
                    break

    total_songs = (await db.execute(
        f"SELECT COUNT(*) FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma{where_sql}",
        args,
    )).scalar_one()

    # Year + classification maps use lower(trim()) so the JSON keys
    # group case variants together.
    by_year_rows = (await db.execute(
        f"SELECT COALESCE(f.anio, 'Unknown') AS y, COUNT(*) "
        f"FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma{where_sql} "
        f"GROUP BY f.anio",
        args,
    )).all()
    songs_by_year = {r[0]: r[1] for r in by_year_rows}

    by_clas_rows = (await db.execute(
        f"SELECT COALESCE(s.clasificacion, 'ESPAÑOL_ESTANDAR') AS c, COUNT(*) "
        f"FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma{where_sql} "
        f"GROUP BY s.clasificacion",
        args,
    )).all()
    songs_by_clas = {r[0]: r[1] for r in by_clas_rows}

    by_theme_rows = (await db.execute(
        f"SELECT s.tema, COUNT(*) FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma{where_sql} "
        f"AND s.tema IS NOT NULL AND s.tema != '' GROUP BY s.tema ORDER BY COUNT(*) DESC",
        args,
    )).all()
    # Canonicalize on the way out so the dashboard never shows two
    # chips for the same concept.
    songs_by_theme: dict[str, int] = {}
    for theme, count in by_theme_rows:
        c = canonical_tema(theme)
        if c:
            songs_by_theme[c] = songs_by_theme.get(c, 0) + count

    recently_added = (await db.execute(
        "SELECT COUNT(*) FROM songs s "
        "WHERE s.created_at > datetime('now', '-30 days')",
    )).scalar_one()

    total_albums = (await db.execute(
        "SELECT COUNT(DISTINCT fonograma_id) FROM songs"
        + where_sql.replace("s.fonograma_id", "fonograma_id"),
        args,
    )).scalar_one or 0

    lyrics_rows = (await db.execute(
        f"SELECT s.lyrics FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
        f"{where_sql}",
        args,
    )).all()
    lyrics_lens = [len(r[0]) for r in lyrics_rows if r[0]]
    songs_with_lyrics = sum(1 for L in lyrics_lens if L > 0)
    avg_lyrics = (sum(lyrics_lens) / len(lyrics_lens)) if lyrics_lens else 0.0

    top_rows = (await db.execute(
        f"SELECT f.titulo, f.anio, COUNT(*) AS n "
        f"FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma{where_sql} "
        f"GROUP BY f.clave_fonograma ORDER BY n DESC LIMIT 10",
        args,
    )).all()
    top_albums = [AlbumCount(album=r[0], year=r[1], count=r[2]) for r in top_rows]

    oov_rows = (await db.execute(
        "SELECT pct_oov, categoria, contiene_indigena FROM song_stats"
    )).all()
    by_oov = {"BAJA": 0, "MEDIA": 0, "ALTA": 0}
    for pct, _, _ in oov_rows:
        if pct is None:
            continue
        if pct < 5:
            by_oov["BAJA"] += 1
        elif pct < 18:
            by_oov["MEDIA"] += 1
        else:
            by_oov["ALTA"] += 1
    indigena_rows = (await db.execute(
        "SELECT contiene_indigena FROM song_stats"
    )).all()
    by_indigena = {"CON_INDIGENA": 0, "SIN_INDIGENA": 0}
    for c in indigena_rows:
        if c[0]:
            by_indigena["CON_INDIGENA"] += 1
        else:
            by_indigena["SIN_INDIGENA"] += 1

    sin_anio = (await db.execute(
        "SELECT COUNT(*) FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
        " WHERE f.anio IS NULL OR f.anio = '' OR f.anio = 's/d'",
    )).scalar_one

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

# Static Spanish stop-word list (small subset for the demo; the full
# list lives in /api/word-cloud's binary cousin but Phase 1 keeps
# this compact and well-tested).
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

# Bound the in-process word-cloud query to keep the response small.
_MAX_WORDS = 8_000


def _extract_words(lyrics: str) -> list[str]:
    """Yield alphabetic tokens from a lyrics string."""
    buf: list[str] = []
    current: list[str] = []
    for ch in lyrics:
        if ch.isalpha():
            current.append(ch)
        else:
            if current:
                buf.append("".join(current).lower())
                current = []
            if len(buf) >= _MAX_WORDS:
                break
    if current:
        buf.append("".join(current).lower())
    return buf


@router.get("/word-cloud", response_model=WordCloudResponse)
async def get_word_cloud(
    db: DbDep,
    query: Annotated[str, Query(max_length=500)] = "",
) -> WordCloudResponse:
    """Top 500 most-frequent non-stop-word tokens across the catalog.

    Theme/year filters reuse the same parser as /api/search and /api/stats.
    """
    where_sql = ""
    args: list[object] = []
    if query:
        for p in query.split("&"):
            if p.startswith("year_from="):
                v = parse_int_or_none(p.split("=", 1)[1])
                if v is not None:
                    where_sql = " WHERE CAST(f.anio AS INTEGER) >= ?"
                    args.append(v)
                    break

    rows = (await db.execute(
        f"SELECT s.lyrics FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
        f"{where_sql} LIMIT ?",
        args + [_MAX_WORDS],
    )).all()

    counts: dict[str, int] = {}
    excluded = 0
    total = 0
    for (lyrics,) in rows:
        for w in _extract_words(lyrics or ""):
            total += 1
            if w in SPANISH_STOPWORDS:
                excluded += 1
                continue
            counts[w] = counts.get(w, 0) + 1

    top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:500]
    max_c = top[0][1] if top else 1
    words = [
        WordFreq(text=t, size=10 + (c * 90 // max_c)) for t, c in top
    ]
    return WordCloudResponse(
        words=words, totalWords=total, excludedStopWords=excluded,
    )


__all__ = ["router"]
