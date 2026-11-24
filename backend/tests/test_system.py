from app.core.config import Settings


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_status_never_leaks_secrets(client, monkeypatch):
    from app.core import config

    secret = "sk-ant-should-never-leak-123"
    config.get_settings.cache_clear()
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    try:
        from fastapi.testclient import TestClient

        from app.main import create_app

        body = TestClient(create_app()).get("/api/system/status").text
        assert secret not in body
        assert '"anthropic"' in body
    finally:
        config.get_settings.cache_clear()


def test_status_reports_components(client):
    data = client.get("/api/system/status").json()
    names = {c["name"] for c in data["components"]}
    assert {"ffmpeg", "whisper", "tts", "anthropic", "youtube"} <= names
    anthropic = next(c for c in data["components"] if c["name"] == "anthropic")
    assert anthropic["available"] is False  # sin clave en tests
    assert data["limits"]["monthly_budget_usd"] > 0


def test_ffmpeg_has_required_codecs(client):
    ff = next(c for c in client.get("/api/system/status").json()["components"]
              if c["name"] == "ffmpeg")
    assert ff["available"], ff["detail"]


def test_settings_configured_flags():
    s = Settings(anthropic_api_key="", youtube_api_key="abc")
    assert not s.anthropic_configured
    assert s.youtube_configured
