from sqlalchemy import select

from app.core.config import get_settings
from app.models import Reference
from app.services import youtube as yt
from app.services.jobs import JobContext, register


@register("refresh_metrics")
def refresh_metrics(ctx: JobContext, payload: dict) -> dict:
    """Toma una nueva medición de cada referencia de YouTube (1 unidad cada 50 videos)."""
    db, settings = ctx.db, get_settings()
    ids = list(db.scalars(select(Reference.youtube_id).where(Reference.youtube_id.is_not(None))))
    updated = 0
    for i in range(0, len(ids), 50):
        videos = yt.fetch_videos(db, settings, ids[i:i + 50])
        yt.record_snapshots(db, videos)
        db.commit()
        updated += len(videos)
        ctx.progress((i + 50) / max(len(ids), 1))
    return {"requested": len(ids), "updated": updated, "missing": len(ids) - updated}
