import pytest

from app.services.youtube_urls import extract_youtube_id


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?t=10",
        "youtube.com/shorts/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ&list=x",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "dQw4w9WgXcQ",
    ],
)
def test_extract_youtube_id(url):
    assert extract_youtube_id(url) == "dQw4w9WgXcQ"


@pytest.mark.parametrize("url", ["https://vimeo.com/123", "https://youtube.com/watch?v=short"])
def test_extract_youtube_id_rejects(url):
    assert extract_youtube_id(url) is None


def test_create_list_update_delete(client):
    r = client.post("/api/references", json={
        "url": "https://youtu.be/dQw4w9WgXcQ", "tags": ["Historia ", "historia", "Misterio"],
        "category": "educación",
    })
    assert r.status_code == 201, r.text
    ref = r.json()
    assert ref["youtube_id"] == "dQw4w9WgXcQ"
    assert ref["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert ref["status"] == "pending_analysis"
    assert sorted(t["name"] for t in ref["tags"]) == ["historia", "misterio"]
    assert ref["growth"]["sufficient_data"] is False

    # duplicado
    dup = client.post("/api/references", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert dup.status_code == 409
    assert dup.json()["detail"]["id"] == ref["id"]

    client.post("/api/references", json={"url": "https://vimeo.com/76979871", "title": "Otro"})

    page = client.get("/api/references").json()
    assert page["total"] == 2
    assert client.get("/api/references", params={"tag": "HISTORIA"}).json()["total"] == 1
    assert client.get("/api/references", params={"q": "otro"}).json()["total"] == 1

    up = client.patch(f"/api/references/{ref['id']}", json={"is_favorite": True, "tags": ["nuevo"]})
    assert up.json()["is_favorite"] is True
    assert [t["name"] for t in up.json()["tags"]] == ["nuevo"]
    assert client.get("/api/references", params={"favorite": True}).json()["total"] == 1
    assert {t["name"] for t in client.get("/api/tags").json()} >= {"nuevo", "historia"}

    assert client.delete(f"/api/references/{ref['id']}").status_code == 204
    assert client.get(f"/api/references/{ref['id']}").status_code == 404


def test_invalid_url(client):
    assert client.post("/api/references", json={"url": "no es una url"}).status_code == 422


def test_dashboard_counts(client):
    client.post("/api/references", json={"url": "https://youtu.be/dQw4w9WgXcQ"})
    d = client.get("/api/dashboard").json()
    assert d["references"] == 1
    assert d["analyzed"] == 0 and d["scripts"] == 0 and d["clips_approved"] == 0
    assert d["usage"]["month_cost_usd"] == 0
