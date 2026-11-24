"""Servidor falso de YouTube Data API v3 (formato real de respuestas) para tests."""

import json
from datetime import UTC, datetime, timedelta

import httpx

from app.services.youtube import YouTubeClient


def video_item(vid: str, views: int, duration: str = "PT45S", days_ago: int = 3,
               category: str = "27", title: str | None = None) -> dict:
    published = (datetime.now(UTC) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "kind": "youtube#video",
        "id": vid,
        "snippet": {
            "publishedAt": published,
            "channelId": "UC123",
            "title": title or f"Video {vid}",
            "description": "desc",
            "thumbnails": {"high": {"url": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"}},
            "channelTitle": "Canal X",
            "categoryId": category,
            "defaultAudioLanguage": "es",
            "tags": ["a", "b"],
        },
        "contentDetails": {"duration": duration},
        "statistics": {"viewCount": str(views), "likeCount": "10", "commentCount": "2"},
    }


class FakeYouTube:
    def __init__(self):
        self.videos: dict[str, dict] = {}
        self.search_results: list[str] = []
        self.requests: list[httpx.Request] = []
        self.fail_with: tuple[int, dict] | None = None

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        assert request.headers.get("X-Goog-Api-Key") == "test-key"
        assert "key" not in request.url.params  # la clave nunca va en la URL
        if self.fail_with:
            status, body = self.fail_with
            return httpx.Response(status, json=body)
        path = request.url.path.rsplit("/", 1)[-1]
        q = request.url.params
        if path == "search":
            assert q["type"] == "video"
            items = [{"id": {"kind": "youtube#video", "videoId": v}} for v in self.search_results]
            return httpx.Response(200, json={"items": items, "nextPageToken": "NEXT",
                                             "pageInfo": {"totalResults": 1000}})
        if path == "videos":
            if q.get("chart") == "mostPopular":
                return httpx.Response(200, json={"items": list(self.videos.values())})
            ids = q["id"].split(",")
            return httpx.Response(200, json={
                "items": [self.videos[i] for i in ids if i in self.videos]})
        if path == "videoCategories":
            return httpx.Response(200, json={"items": [
                {"id": "27", "snippet": {"title": "Educación", "assignable": True}},
                {"id": "18", "snippet": {"title": "Short Movies", "assignable": False}},
            ]})
        return httpx.Response(404, json={"error": {"message": "not found"}})

    def client(self) -> YouTubeClient:
        return YouTubeClient("test-key", httpx.Client(transport=httpx.MockTransport(self.handler)))

    def last_params(self, path: str) -> dict:
        for r in reversed(self.requests):
            if r.url.path.endswith(path):
                return dict(r.url.params)
        raise AssertionError(path)


def dumps(o) -> str:
    return json.dumps(o)
