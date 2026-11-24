from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import Settings
from app.core.errors import ProviderDisabled, UsageLimitExceeded
from app.services import jobs, usage
from app.services.metrics import compute_growth


def test_growth_requires_two_snapshots():
    t = datetime(2026, 1, 1, tzinfo=UTC)
    assert compute_growth([]).sufficient_data is False
    assert compute_growth([(t, 100)]).sufficient_data is False
    g = compute_growth([(t, 100), (t + timedelta(hours=2), 300), (t + timedelta(hours=3), 600)])
    assert g.sufficient_data and g.snapshots == 3
    assert g.views_per_hour_recent == 300
    assert g.views_per_hour_overall == pytest.approx(500 / 3, rel=1e-3)


def test_anthropic_cost():
    s = Settings(anthropic_input_usd_per_mtok=4, anthropic_output_usd_per_mtok=20)
    assert usage.anthropic_cost(s, 1_000_000, 100_000) == pytest.approx(6.0)


def test_limits(db):
    s = Settings(anthropic_api_key="k", youtube_api_key="k", limit_claude_calls_per_day=2,
                 limit_youtube_units_per_day=150, limit_monthly_budget_usd=1.0)
    usage.ensure_allowed(db, s, "anthropic")
    usage.record(db, "anthropic", "analysis", cost_usd=0.1)
    usage.record(db, "anthropic", "analysis", cost_usd=0.1)
    with pytest.raises(UsageLimitExceeded):
        usage.ensure_allowed(db, s, "anthropic")

    usage.ensure_allowed(db, s, "youtube", units=100)
    usage.record(db, "youtube", "search.list", units=100)
    with pytest.raises(UsageLimitExceeded):
        usage.ensure_allowed(db, s, "youtube", units=100)

    s2 = Settings(anthropic_api_key="k", limit_monthly_budget_usd=0.15)
    with pytest.raises(UsageLimitExceeded, match="Presupuesto"):
        usage.ensure_allowed(db, s2, "anthropic")


def test_provider_disabled(db):
    with pytest.raises(ProviderDisabled):
        usage.ensure_allowed(db, Settings(anthropic_api_key=""), "anthropic")
    with pytest.raises(ProviderDisabled):
        usage.ensure_allowed(db, Settings(youtube_api_key="k", youtube_enabled=False), "youtube")


def test_job_success_and_failure(db):
    @jobs.register("test_ok")
    def ok(ctx, payload):
        ctx.progress(0.5)
        return {"doubled": payload["n"] * 2}

    @jobs.register("test_fail")
    def fail(ctx, payload):
        raise ValueError("boom")

    a = jobs.enqueue(db, "test_ok", {"n": 21})
    b = jobs.enqueue(db, "test_fail", {})
    assert jobs.run_pending_once() == 2
    db.expire_all()
    from app.models import Job

    ja, jb = db.get(Job, a.id), db.get(Job, b.id)
    assert ja.status == "succeeded" and ja.result == {"doubled": 42} and ja.progress == 1.0
    assert jb.status == "failed" and "boom" in jb.error
    with pytest.raises(ValueError):
        jobs.enqueue(db, "desconocido", {})


def test_render_selftest_job(client):
    job = client.post("/api/system/selftest").json()
    assert job["status"] == "queued"
    jobs.run_pending_once()
    done = client.get(f"/api/jobs/{job['id']}").json()
    assert done["status"] == "succeeded", done["error"]
    assert done["result"]["video"] == "h264 1080x1920"
    assert done["result"]["audio"] == "aac"
