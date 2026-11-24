import pytest

from app.core import config
from app.services import jobs
from app.services import youtube as yt
from app.services.youtube import parse_iso8601_duration
from tests.fake_youtube import FakeYouTube, video_item


@pytest.mark.parametrize("raw,secs", [
    ("PT45S", 45), ("PT1M", 60), ("PT1H2M3S", 3723), ("P1DT1S", 86401), ("PT0S", 0),
    ("garbage", None), (None, None),
])
def test_parse_duration(raw, secs):
    assert parse_iso8601_duration(raw) == secs


@pytest.fixture()
def fake(monkeypatch):
    f = FakeYouTube()
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")
    config.get_settings.cache_clear()
    monkeypatch.setattr(yt, "client_factory", lambda s: f.client())
    yt._category_cache.clear()
    yield f
    config.get_settings.cache_clear()


def test_search_without_key_is_503(client):
    r = client.post("/api/radar/search", json={"q": "historia"})
    assert r.status_code == 503
    assert "YOUTUBE_API_KEY" in r.json()["detail"]


def test_search_filters_and_quota(fake, client):
    fake.videos = {
        "aaaaaaaaaaa": video_item("aaaaaaaaaaa", 1000, "PT45S"),
        "bbbbbbbbbbb": video_item("bbbbbbbbbbb", 5000, "PT10M"),
        "ccccccccccc": video_item("ccccccccccc", 3000, "PT30S"),
    }
    fake.search_results = list(fake.videos)
    r = client.post("/api/radar/search", json={
        "q": "misterios", "language": "es", "region": "AR", "max_age_days": 30,
        "duration": "short", "max_seconds": 60, "category_id": "27",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    # filtro preciso por duración + orden por vistas
    assert [v["youtube_id"] for v in body["videos"]] == ["ccccccccccc", "aaaaaaaaaaa"]
    assert body["filtered_out"] == 1
    v = body["videos"][0]
    assert v["duration_seconds"] == 30 and v["view_count"] == 3000
    assert v["growth"]["sufficient_data"] is False  # una sola medición
    assert v["avg_views_per_day"] == pytest.approx(1000, rel=0.01)
    assert v["reference_id"] is None
    p = fake.last_params("search")
    assert p["relevanceLanguage"] == "es" and p["regionCode"] == "AR"
    assert p["videoDuration"] == "short" and p["videoCategoryId"] == "27"
    assert p["order"] == "viewCount" and "publishedAfter" in p
    usage = client.get("/api/dashboard").json()["usage"]
    assert usage["youtube_units_today"] == 101


def test_growth_after_two_searches(fake, client, db):
    from datetime import timedelta

    from sqlalchemy import select

    from app.models import MetricSnapshot

    fake.videos = {"aaaaaaaaaaa": video_item("aaaaaaaaaaa", 1000)}
    fake.search_results = ["aaaaaaaaaaa"]
    first = client.post("/api/radar/search", json={"q": "x"}).json()
    assert first["videos"][0]["growth"]["sufficient_data"] is False
    # Simular que la primera medición fue hace 2 horas.
    for snap in db.scalars(select(MetricSnapshot)):
        snap.captured_at = snap.captured_at - timedelta(hours=2)
    db.commit()
    fake.videos["aaaaaaaaaaa"]["statistics"]["viewCount"] = "1600"
    g = client.post("/api/radar/search", json={"q": "x"}).json()["videos"][0]["growth"]
    assert g["sufficient_data"] is True and g["snapshots"] == 2
    assert g["view_delta"] == 600
    assert g["views_per_hour_recent"] == pytest.approx(300, rel=0.01)


def test_trending_mode_costs_one_unit(fake, client):
    fake.videos = {"aaaaaaaaaaa": video_item("aaaaaaaaaaa", 10)}
    r = client.post("/api/radar/search", json={"mode": "trending", "region": "ar",
                                               "category_id": "27"})
    assert r.status_code == 200
    assert fake.last_params("videos")["chart"] == "mostPopular"
    assert client.get("/api/dashboard").json()["usage"]["youtube_units_today"] == 1


def test_search_requires_query_or_category(fake, client):
    assert client.post("/api/radar/search", json={"q": ""}).status_code == 422


def test_save_and_refresh_and_snapshots(fake, client):
    fake.videos = {"aaaaaaaaaaa": video_item("aaaaaaaaaaa", 1000, "PT1M5S", title="Título real")}
    fake.search_results = ["aaaaaaaaaaa"]
    client.get("/api/radar/categories", params={"region": "AR", "hl": "es"})
    client.post("/api/radar/search", json={"q": "x"})
    saved = client.post("/api/radar/save", json={"youtube_ids": ["aaaaaaaaaaa", "aaaaaaaaaaa"],
                                                 "tags": ["radar"]})
    assert saved.status_code == 201, saved.text
    ref = saved.json()[0]
    assert ref["title"] == "Título real" and ref["duration_seconds"] == 65
    assert ref["category"] == "Educación" and ref["channel_title"] == "Canal X"
    assert ref["published_at"] and ref["description"] == "desc"
    # guardar de nuevo no duplica
    assert client.post("/api/radar/save", json={"youtube_ids": ["aaaaaaaaaaa"]}).json() == []

    fake.videos["aaaaaaaaaaa"]["statistics"]["viewCount"] = "2500"
    r = client.post(f"/api/references/{ref['id']}/refresh").json()
    assert r["view_count"] == 2500
    snaps = client.get(f"/api/references/{ref['id']}/snapshots").json()
    # búsqueda + guardado + refresh = 3 mediciones históricas del mismo video
    assert [s["view_count"] for s in snaps] == [1000, 1000, 2500]

    # la búsqueda marca el video como guardado
    body = client.post("/api/radar/search", json={"q": "x"}).json()
    assert body["videos"][0]["reference_id"] == ref["id"]


def test_manual_url_enriched(fake, client):
    fake.videos = {"dQw4w9WgXcQ": video_item("dQw4w9WgXcQ", 42, title="Real")}
    r = client.post("/api/references", json={"url": "https://youtu.be/dQw4w9WgXcQ"}).json()
    assert r["title"] == "Real" and r["view_count"] == 42


def test_manual_url_survives_youtube_error(fake, client):
    fake.fail_with = (403, {"error": {"message": "quota", "errors": [{"reason": "quotaExceeded"}]}})
    r = client.post("/api/references", json={"url": "https://youtu.be/dQw4w9WgXcQ"})
    assert r.status_code == 201
    assert r.json()["title"] == "YouTube dQw4w9WgXcQ"


def test_quota_error_translated(fake, client):
    fake.fail_with = (403, {"error": {"message": "x", "errors": [{"reason": "quotaExceeded"}]}})
    r = client.post("/api/radar/search", json={"q": "x"})
    assert r.status_code == 429 and "cuota" in r.json()["detail"]


def test_local_quota_limit(fake, client, monkeypatch):
    monkeypatch.setenv("LIMIT_YOUTUBE_UNITS_PER_DAY", "150")
    config.get_settings.cache_clear()
    fake.search_results = []
    assert client.post("/api/radar/search", json={"q": "x"}).status_code == 200
    r = client.post("/api/radar/search", json={"q": "x"})
    assert r.status_code == 429 and "Cuota diaria" in r.json()["detail"]
    assert len([x for x in fake.requests if x.url.path.endswith("search")]) == 1


def test_refresh_metrics_job(fake, client):
    fake.videos = {"aaaaaaaaaaa": video_item("aaaaaaaaaaa", 5)}
    client.post("/api/radar/save", json={"youtube_ids": ["aaaaaaaaaaa"]})
    fake.videos["aaaaaaaaaaa"]["statistics"]["viewCount"] = "9"
    job_id = client.post("/api/references/refresh-metrics").json()["job_id"]
    jobs.run_pending_once()
    job = client.get(f"/api/jobs/{job_id}").json()
    assert job["status"] == "succeeded", job["error"]
    assert job["result"] == {"requested": 1, "updated": 1, "missing": 0}
    ref = client.get("/api/references").json()["items"][0]
    assert ref["view_count"] == 9 and ref["growth"]["snapshots"] == 2
