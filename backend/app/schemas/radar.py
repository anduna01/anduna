from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.references import GrowthOut


class RadarSearch(BaseModel):
    mode: Literal["search", "trending"] = "search"
    q: str | None = Field(default=None, max_length=200)
    category_id: str | None = Field(default=None, pattern=r"^\d{1,4}$")
    language: str | None = Field(default=None, pattern=r"^[a-zA-Z]{2,3}(-[A-Za-z]{2,4})?$")
    region: str | None = Field(default=None, pattern=r"^[A-Za-z]{2}$")
    max_age_days: int | None = Field(default=None, ge=1, le=3650)
    duration: Literal["short", "medium", "long"] | None = None
    min_seconds: int | None = Field(default=None, ge=0)
    max_seconds: int | None = Field(default=None, ge=1)
    order: Literal["viewCount", "date", "relevance", "rating"] = "viewCount"
    max_results: int = Field(default=25, ge=1, le=50)
    page_token: str | None = Field(default=None, max_length=200)


class RadarVideo(BaseModel):
    youtube_id: str
    url: str
    title: str
    channel_title: str | None
    published_at: datetime | None
    duration_seconds: int | None
    thumbnail_url: str | None
    language: str | None
    category_id: str | None
    view_count: int | None
    like_count: int | None
    comment_count: int | None
    # Promedio desde la publicación (una sola medición): NO es crecimiento.
    avg_views_per_day: float | None
    growth: GrowthOut
    reference_id: int | None


class RadarResult(BaseModel):
    videos: list[RadarVideo]
    next_page_token: str | None
    total_results: int | None
    filtered_out: int


class RadarSave(BaseModel):
    youtube_ids: list[str] = Field(min_length=1, max_length=50)
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] = Field(default_factory=list)


class SnapshotOut(BaseModel):
    captured_at: datetime
    view_count: int | None
    like_count: int | None
    comment_count: int | None
