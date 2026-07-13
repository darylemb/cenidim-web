"""End-to-end tests for /api/* (public catalogue endpoints).

Seeds a small but representative dataset (3 fonogramas, 4 songs,
1 stats row) so the SQL aggregates have something to chew on.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app import db as db_module
from app.models.fonograma import Fonograma
from app.models.song import Song
from app.models.song_stats import SongStats
from app.models.theme_normalization import canonical_tema


async def _seed(db_session) -> None:
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        session.add_all([
            Fonograma(
                clave_fonograma=10,
                titulo="Album Uno",
                subtitulo=None,
                interprete_principal="Author One",
                anio="1950",
            ),
            Fonograma(
                clave_fonograma=20,
                titulo="Album Dos",
                anio="1975",
            ),
            Fonograma(
                clave_fonograma=30,
                titulo="Album Tres",
                anio="1990",
            ),
        ])
        await session.flush()
        songs = [
            Song(
                fonograma_id=10,
                title="Track A",
                lyrics="hello world this is a long lyric",
                clasificacion="corrido",
                tema="Vida/ muerte",
                autor="Author One",
                duracion="03:21",
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
            ),
            Song(
                fonograma_id=10,
                title="Track B",
                lyrics="otra canción con palabras distintas",
                clasificacion="romance",
                tema="amor",
                autor="Author Two",
                duracion="02:45",
                created_at=datetime(2024, 1, 2, tzinfo=UTC),
            ),
            Song(
                fonograma_id=20,
                title="Track C",
                lyrics="the quick brown fox jumps over the lazy dog",
                clasificacion="corrido",
                tema="Vida/Muerte",  # canonical = Vida/Muerte
                duracion="04:10",
                created_at=datetime(2024, 2, 1, tzinfo=UTC),
            ),
            Song(
                fonograma_id=30,
                title="Track D",
                lyrics=None,
                clasificacion=None,
                tema=None,
                created_at=datetime(2024, 3, 1, tzinfo=UTC),
            ),
        ]
        session.add_all(songs)
        await session.flush()
        session.add(
            SongStats(
                song_id=songs[0].id,
                pct_oov=2.0,   # BAJA bucket (<5)
                categoria="medium",
                contiene_indigena=0,
                n_tokens=15,
            )
        )
        session.add(
            SongStats(
                song_id=songs[1].id,
                pct_oov=10.0,  # MEDIA bucket (<18)
                categoria="medium",
                contiene_indigena=1,  # CON_INDIGENA bucket
                n_tokens=15,
            )
        )
        session.add(
            SongStats(
                song_id=songs[2].id,
                pct_oov=25.0,  # ALTA bucket (>=18)
                categoria="alta",
                contiene_indigena=0,
                n_tokens=20,
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_search_returns_empty(app_client, db_session):
    response = await app_client.get("/api/search")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["results"] == []


@pytest.mark.asyncio
async def test_search_by_title(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/search", params={"q": "Track A", "field": "title"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    titles = [r["title"] for r in body["results"]]
    assert "Track A" in titles


@pytest.mark.asyncio
async def test_search_by_lyrics(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/search",
        params={"q": "quick brown fox", "field": "lyrics"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["title"] == "Track C"


@pytest.mark.asyncio
async def test_search_by_album(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/search",
        params={"q": "Album Uno", "field": "album"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert all(r["fonograma_id"] == 10 for r in body["results"])


@pytest.mark.asyncio
async def test_search_by_year_range(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/search", params={"year_from": 1970, "year_to": 1980})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["results"][0]["fonograma_id"] == 20


@pytest.mark.asyncio
async def test_search_inverted_year_range_returns_400(app_client, db_session):
    response = await app_client.get("/api/search", params={"year_from": 1990, "year_to": 1950})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_filters_by_clasificacion(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/search",
        params={"clasificacion": "corrido"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert all(r["clasificacion"] == "corrido" for r in body["results"])


@pytest.mark.asyncio
async def test_search_filters_by_tema_canonical(app_client, db_session):
    await _seed(db_session)
    # Vida/ muerte and Vida/Muerte should match the same bucket.
    response = await app_client.get("/api/search", params={"tema": "Vida/ muerte"})
    assert response.status_code == 200
    body = response.json()
    # Both A and C have tema that canonicalizes to Vida/Muerte
    assert body["total"] == 2


@pytest.mark.asyncio
async def test_search_filters_by_tema_love(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/search", params={"tema": "amor"})
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_filters_by_album_eq(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/search", params={"album": "Album Dos"})
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_pagination(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/search", params={"page": 1, "limit": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 4
    assert len(body["results"]) == 2
    response = await app_client.get("/api/search", params={"page": 2, "limit": 2})
    assert len(response.json()["results"]) == 2


@pytest.mark.asyncio
async def test_search_order_by_title_desc(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/search", params={"order_by": "title", "order_dir": "desc"}
    )
    assert response.status_code == 200
    titles = [r["title"] for r in response.json()["results"]]
    assert titles == sorted(titles, reverse=True)


@pytest.mark.asyncio
async def test_search_order_by_year(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/search", params={"order_by": "year"})
    assert response.status_code == 200
    body = response.json()
    # 1950 < 1975 < 1990
    years = [int(r["fonograma_id"]) for r in body["results"]]
    # First two songs are fonograma 10 (1950), then 20 (1975), then 30 (1990).
    assert years == [10, 10, 20, 30]


@pytest.mark.asyncio
async def test_search_q_too_long(app_client, db_session):
    response = await app_client.get("/api/search", params={"q": "x" * 201})
    # FastAPI's Query(max_length=200) rejects before our handler runs.
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_field_lyrics(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/search", params={"q": "brown fox", "field": "lyrics"}
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_field_album(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/search", params={"q": "Album Uno", "field": "album"}
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2


@pytest.mark.asyncio
async def test_timeline_year_to_filter(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/timeline", params={"query": "year_to=1960"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "1950" in body["years"]
    assert "1975" not in body["years"]


@pytest.mark.asyncio
async def test_word_cloud_with_year_filter(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/word-cloud", params={"query": "year_from=1990"}
    )
    assert response.status_code == 200
    body = response.json()
    # Track D has lyrics=None, so no words at all in 1990+ range.
    assert body["totalWords"] == 0


@pytest.mark.asyncio
async def test_search_invalid_order_by_returns_422(app_client, db_session):
    response = await app_client.get("/api/search", params={"order_by": "evil"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_song_detail(app_client, db_session):
    await _seed(db_session)
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select as _sel

        first = (await session.execute(_sel(Song))).scalars().first()
        sid = first.id

    response = await app_client.get(f"/api/song/{sid}")
    assert response.status_code == 200
    assert response.json()["id"] == sid
    assert response.json()["title"] == first.title


@pytest.mark.asyncio
async def test_get_song_detail_404(app_client, db_session):
    response = await app_client.get("/api/song/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_song_detail_invalid_id(app_client, db_session):
    response = await app_client.get("/api/song/notanint")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stats_endpoint(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_songs"] == 4
    assert body["total_albums"] == 3
    assert body["songs_with_lyrics"] == 3
    assert body["songs_by_clasificacion"].get("corrido", 0) == 2
    assert body["songs_by_clasificacion"].get("romance", 0) == 1
    # Vida/Muerte appears twice (A + C); amor once; None ignored
    assert body["songs_by_theme"].get("Vida/Muerte", 0) == 2
    assert body["songs_by_theme"].get("Amor", 0) == 1
    assert body["songs_by_year"]["1950"] == 2
    assert body["songs_by_year"]["1975"] == 1
    assert body["songs_by_year"]["1990"] == 1
    # OOV buckets: BAJA=1 (songs[0]), MEDIA=1 (songs[1]), ALTA=1 (songs[2])
    assert body["songs_by_oov_level"]["BAJA"] == 1
    assert body["songs_by_oov_level"]["MEDIA"] == 1
    assert body["songs_by_oov_level"]["ALTA"] == 1
    # Indigena buckets
    assert body["songs_by_indigena"]["CON_INDIGENA"] == 1
    assert body["songs_by_indigena"]["SIN_INDIGENA"] == 2


@pytest.mark.asyncio
async def test_stats_with_year_from_filter(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get(
        "/api/stats", params={"query": "year_from=1970"}
    )
    assert response.status_code == 200
    body = response.json()
    # Filtered to 1975+ -> only Track C (1975) + Track D (1990) = 2 songs.
    assert body["total_songs"] == 2
    assert body["songs_by_year"].get("1950") is None


@pytest.mark.asyncio
async def test_timeline_endpoint(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/timeline")
    assert response.status_code == 200
    body = response.json()
    assert "1950" in body["years"]
    assert "1975" in body["years"]
    assert body["total"] >= 4


@pytest.mark.asyncio
async def test_word_cloud_endpoint(app_client, db_session):
    await _seed(db_session)
    response = await app_client.get("/api/word-cloud")
    assert response.status_code == 200
    body = response.json()
    assert "words" in body
    assert isinstance(body["words"], list)
    if body["words"]:
        first = body["words"][0]
        assert "text" in first
        assert "size" in first


def test_canonical_tema_isolated():
    # Direct unit call so the SQL doesn't need to run.
    assert canonical_tema("Vida/ muerte") == "Vida/Muerte"
    assert canonical_tema("vida/mUERTE") == "Vida/Muerte"
    assert canonical_tema("") == ""
    assert canonical_tema(None) == ""
