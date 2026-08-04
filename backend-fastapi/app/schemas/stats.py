"""Stats DTOs."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AlbumCount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    album: str
    year: str
    count: int


class StatsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_songs: int
    total_albums: int
    catalog_total: int
    recently_added: int
    songs_with_lyrics: int
    avg_lyrics_length: float
    songs_by_year: dict[str, int]
    songs_by_clasificacion: dict[str, int]
    songs_by_theme: dict[str, int]
    distinct_themes: int
    top_albums: list[AlbumCount] = Field(default_factory=list)
    songs_by_oov_level: dict[str, int] = Field(default_factory=dict)
    songs_by_indigena: dict[str, int] = Field(default_factory=dict)
    songs_without_year: int


class TimelineData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    years: list[str]
    timeline: dict[str, list[dict]]
    total: int
    truncated: bool


class WordFreq(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    text: str
    size: int


class WordCloudResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    words: list[WordFreq]
    totalWords: int
    excludedStopWords: int


class PaginatedResponse(BaseModel):
    """Generic pagination envelope for /api/admin/* list endpoints."""
    model_config = ConfigDict(extra="forbid")

    results: list[dict]
    total: int
    page: int = 1
    limit: int = 20


__all__ = [
    "AlbumCount",
    "PaginatedResponse",
    "StatsResponse",
    "TimelineData",
    "WordCloudResponse",
    "WordFreq",
]
