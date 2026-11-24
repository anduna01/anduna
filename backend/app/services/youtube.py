"""Cliente de YouTube Data API v3 y operaciones del radar.

- La clave viaja en el header `X-Goog-Api-Key` (no en la URL → no queda en logs).
- Cada llamada consume cuota: se valida con `usage.ensure_allowed` y se registra.
- Sólo se consultan metadatos públicos. Nunca se descarga material audiovisual.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import MetricSnapshot, Reference
from app.services import usage
from app.services.youtube_urls import canonical_url

API_BASE = "https://www.googleapis.com/youtube/v3"

# Duración aproximada que acepta search.list (filtro grueso del lado de YouTube).
YT_DURATION = {"short": "short", "medium": "medium", "long": "long"}  # <4m, 4-20m, >20m
ORDERS = {"viewCount", "date", "relevance", "rating"}


class YouTubeError(Exception):
    """Error devuelto por la API de YouTube, con mensaje apto para el usuario."""

    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


def parse_iso8601_duration(value: str | None) -> int | None:
    """'PT1H2M3S' → 3723. Devuelve None si no se puede interpretar."""
    if not value:
        return None
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", value)
    if not m:
        return None
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass
class VideoInfo:
    youtube_id: str
    title: str
    channel_title: str | None
    channel_id: str | None
    published_at: datetime | None
    duration_seconds: int | None
    description: str | None
    thumbnail_url: str | None
    language: str | None
    category_id: str | None
    view_count: int | None
    like_count: int | None
    comment_count: int | None
    tags: list[str] = field(default_factory=list)

    @property
    def url(self) -> str:
        return canonical_url(self.youtube_id)

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> VideoInfo:
        sn = item.get("snippet", {})
        st = item.get("statistics", {})
        cd = item.get("contentDetails", {})
        thumbs = sn.get("thumbnails", {})
        thumb = next(
            (thumbs[k]["url"] for k in ("maxres", "standard", "high", "medium", "default")
             if k in thumbs),
            None,
        )
        return cls(
            youtube_id=item["id"],
            title=sn.get("title", ""),
            channel_title=sn.get("channelTitle"),
            channel_id=sn.get("channelId"),
            published_at=_parse_dt(sn.get("publishedAt")),
            duration_seconds=parse_iso8601_duration(cd.get("duration")),
            description=sn.get("description"),
            thumbnail_url=thumb,
            language=sn.get("defaultAudioLanguage") or sn.get("defaultLanguage"),
            category_id=sn.get("categoryId"),
            view_count=_int(st.get("viewCount")),
            like_count=_int(st.get("likeCount")),
            comment_count=_int(st.get("commentCount")),
            tags=list(sn.get("tags") or [])[:30],
        )


@dataclass
class SearchParams:
    q: str | None = None
    mode: str = "search"  # search | trending
    category_id: str | None = None
    language: str | None = None  # relevanceLanguage (ISO 639-1)
    region: str | None = None  # ISO 3166-1 alpha-2
    max_age_days: int | None = None
    duration: str | None = None  # short | medium | long
    min_seconds: int | None = None
    max_seconds: int | None = None
    order: str = "viewCount"
    max_results: int = 25
    page_token: str | None = None


class YouTubeClient:
    def __init__(self, api_key: str, http: httpx.Client | None = None,
                 base_url: str = API_BASE):
        self._key = api_key
        self._http = http or httpx.Client(timeout=20)
        self._base = base_url.rstrip("/")

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        clean = {k: v for k, v in params.items() if v not in (None, "")}
        try:
            r = self._http.get(f"{self._base}/{path}", params=clean,
                               headers={"X-Goog-Api-Key": self._key})
        except httpx.HTTPError as e:
            raise YouTubeError(f"No se pudo contactar a YouTube: {type(e).__name__}") from e
        if r.status_code >= 400:
            raise _translate_error(r)
        return r.json()

    def search_ids(self, p: SearchParams) -> tuple[list[str], str | None, int | None]:
        published_after = None
        if p.max_age_days:
            published_after = (datetime.now(UTC) - timedelta(days=p.max_age_days)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        data = self._get("search", {
            "part": "id",
            "type": "video",
            "q": p.q,
            "videoCategoryId": p.category_id,
            "relevanceLanguage": p.language,
            "regionCode": p.region,
            "publishedAfter": published_after,
            "videoDuration": YT_DURATION.get(p.duration or ""),
            "order": p.order if p.order in ORDERS else "viewCount",
            "maxResults": max(1, min(50, p.max_results)),
            "pageToken": p.page_token,
            "safeSearch": "moderate",
        })
        ids = [it["id"]["videoId"] for it in data.get("items", [])
               if it.get("id", {}).get("videoId")]
        return ids, data.get("nextPageToken"), data.get("pageInfo", {}).get("totalResults")

    def most_popular(self, p: SearchParams) -> tuple[list[dict[str, Any]], str | None]:
        data = self._get("videos", {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": p.region or "US",
            "videoCategoryId": p.category_id,
            "hl": p.language,
            "maxResults": max(1, min(50, p.max_results)),
            "pageToken": p.page_token,
        })
        return data.get("items", []), data.get("nextPageToken")

    def videos(self, ids: list[str]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for i in range(0, len(ids), 50):
            data = self._get("videos", {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(ids[i:i + 50]),
            })
            out.extend(data.get("items", []))
        return out

    def categories(self, region: str, hl: str | None) -> list[dict[str, str]]:
        data = self._get("videoCategories", {"part": "snippet", "regionCode": region, "hl": hl})
        return [
            {"id": it["id"], "title": it["snippet"]["title"]}
            for it in data.get("items", [])
            if it.get("snippet", {}).get("assignable")
        ]


def _translate_error(r: httpx.Response) -> YouTubeError:
    try:
        err = r.json().get("error", {})
        reason = (err.get("errors") or [{}])[0].get("reason", "")
        message = err.get("message", "")
    except ValueError:
        reason, message = "", r.text[:200]
    if reason in {"quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded"}:
        return YouTubeError("YouTube rechazó la consulta: cuota diaria agotada.", 429)
    if reason in {"keyInvalid", "badRequest"} and "key" in message.lower():
        return YouTubeError("La clave de YouTube es inválida. Revisá YOUTUBE_API_KEY.", 503)
    if r.status_code == 403:
        return YouTubeError(
            f"YouTube denegó el acceso ({reason or r.status_code}). Verificá que la API esté "
            "habilitada en el proyecto de Google Cloud.", 503)
    return YouTubeError(f"Error de YouTube {r.status_code}: {message or reason}", 502)


# Fábrica reemplazable (tests).
ClientFactory = Callable[[Settings], YouTubeClient]


def default_factory(settings: Settings) -> YouTubeClient:
    assert settings.youtube_api_key is not None
    return YouTubeClient(settings.youtube_api_key.get_secret_value(),
                         base_url=settings.youtube_api_base)


client_factory: ClientFactory = default_factory


def get_client(db: Session, settings: Settings, units: int) -> YouTubeClient:
    usage.ensure_allowed(db, settings, "youtube", units=units)
    return client_factory(settings)


# ---------------------------------------------------------------------------
# Operaciones de alto nivel
# ---------------------------------------------------------------------------


def record_snapshots(db: Session, videos: list[VideoInfo]) -> None:
    if not videos:
        return
    refs = {
        r.youtube_id: r
        for r in db.scalars(
            select(Reference).where(Reference.youtube_id.in_([v.youtube_id for v in videos]))
        )
    }
    now = datetime.now(UTC)
    for v in videos:
        ref = refs.get(v.youtube_id)
        db.add(MetricSnapshot(youtube_id=v.youtube_id, reference_id=ref.id if ref else None,
                              view_count=v.view_count, like_count=v.like_count,
                              comment_count=v.comment_count, captured_at=now))
        if ref:
            apply_metrics(ref, v, now)


def apply_metrics(ref: Reference, v: VideoInfo, when: datetime | None = None) -> None:
    ref.view_count, ref.like_count, ref.comment_count = v.view_count, v.like_count, v.comment_count
    ref.last_fetched_at = when or datetime.now(UTC)


def apply_metadata(ref: Reference, v: VideoInfo, category_title: str | None = None) -> None:
    ref.source = "youtube"
    ref.youtube_id = v.youtube_id
    ref.url = v.url
    ref.title = v.title
    ref.channel_title = v.channel_title
    ref.channel_id = v.channel_id
    ref.published_at = v.published_at
    ref.duration_seconds = v.duration_seconds
    ref.description = v.description
    ref.thumbnail_url = v.thumbnail_url
    ref.language = v.language
    ref.category_id = v.category_id
    if category_title and not ref.category:
        ref.category = category_title
    apply_metrics(ref, v)


def _within_duration(v: VideoInfo, p: SearchParams) -> bool:
    if v.duration_seconds is None:
        return p.min_seconds is None and p.max_seconds is None
    if p.min_seconds is not None and v.duration_seconds < p.min_seconds:
        return False
    return not (p.max_seconds is not None and v.duration_seconds > p.max_seconds)


def search(db: Session, settings: Settings, p: SearchParams) -> dict[str, Any]:
    """Búsqueda del radar. Devuelve videos enriquecidos y registra una medición de cada uno."""
    if p.mode == "trending":
        client = get_client(db, settings, units=1)
        items, next_token = client.most_popular(p)
        usage.record(db, "youtube", "videos.list", units=1, meta={"chart": "mostPopular"})
        total = None
    else:
        if not (p.q or p.category_id):
            raise ValueError("Ingresá una palabra clave o elegí una categoría.")
        client = get_client(db, settings, units=101)
        ids, next_token, total = client.search_ids(p)
        usage.record(db, "youtube", "search.list", units=100, meta={"q": p.q})
        items = client.videos(ids) if ids else []
        if ids:
            usage.record(db, "youtube", "videos.list", units=(len(ids) + 49) // 50)
    videos = [VideoInfo.from_api(it) for it in items]
    record_snapshots(db, videos)
    db.commit()
    filtered = [v for v in videos if _within_duration(v, p)]
    if p.order == "viewCount":
        filtered.sort(key=lambda v: v.view_count or 0, reverse=True)
    return {"videos": filtered, "next_page_token": next_token, "total_results": total,
            "filtered_out": len(videos) - len(filtered)}


def fetch_videos(db: Session, settings: Settings, ids: list[str]) -> list[VideoInfo]:
    units = (len(ids) + 49) // 50
    client = get_client(db, settings, units=units)
    items = client.videos(ids)
    usage.record(db, "youtube", "videos.list", units=units)
    return [VideoInfo.from_api(it) for it in items]


_category_cache: dict[tuple[str, str | None], list[dict[str, str]]] = {}


def categories(db: Session, settings: Settings, region: str, hl: str | None) -> list[dict]:
    key = (region.upper(), hl)
    if key not in _category_cache:
        client = get_client(db, settings, units=1)
        _category_cache[key] = client.categories(region.upper(), hl)
        usage.record(db, "youtube", "videoCategories.list", units=1)
    return _category_cache[key]


def category_title(db: Session, settings: Settings, category_id: str | None) -> str | None:
    if not category_id:
        return None
    for cache in _category_cache.values():
        for c in cache:
            if c["id"] == category_id:
                return c["title"]
    return None
