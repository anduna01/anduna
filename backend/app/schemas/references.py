from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class GrowthOut(BaseModel):
    snapshots: int
    sufficient_data: bool
    views_per_hour_recent: float | None = None
    views_per_hour_overall: float | None = None
    view_delta: int | None = None
    hours_span: float | None = None


class ReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    youtube_id: str | None
    title: str
    channel_title: str | None
    url: str
    thumbnail_url: str | None
    published_at: datetime | None
    duration_seconds: int | None
    description: str | None
    language: str | None
    region: str | None
    category: str | None
    view_count: int | None
    like_count: int | None
    comment_count: int | None
    last_fetched_at: datetime | None
    is_favorite: bool
    notes: str | None
    status: str
    created_at: datetime
    tags: list[TagOut]
    growth: GrowthOut | None = None


class ReferencePage(BaseModel):
    items: list[ReferenceOut]
    total: int
    limit: int
    offset: int


class ReferenceCreateFromUrl(BaseModel):
    url: str = Field(min_length=3, max_length=1000)
    title: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class ReferenceUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=64)
    is_favorite: bool | None = None
    notes: str | None = None
    tags: list[str] | None = None


class ManualUrl(BaseModel):
    url: HttpUrl
