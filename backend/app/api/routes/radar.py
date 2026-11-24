from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import Reference
from app.schemas.radar import RadarResult, RadarSave, RadarSearch, RadarVideo
from app.schemas.references import GrowthOut, ReferenceOut
from app.services import jobs
from app.services import references as ref_svc
from app.services import youtube as yt

router = APIRouter(tags=["radar"])


def _avg_per_day(v: yt.VideoInfo) -> float | None:
    if v.view_count is None or v.published_at is None:
        return None
    days = (datetime.now(UTC) - v.published_at).total_seconds() / 86400
    return round(v.view_count / max(days, 1 / 24), 1)


@router.get("/radar/categories")
def categories(
    region: str = Query("US", pattern=r"^[A-Za-z]{2}$"),
    hl: str | None = Query(None, pattern=r"^[a-zA-Z]{2,3}(-[A-Za-z]{2,4})?$"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    return yt.categories(db, settings, region, hl)


@router.post("/radar/search", response_model=RadarResult)
def search(body: RadarSearch, db: Session = Depends(get_db),
           settings: Settings = Depends(get_settings)):
    params = yt.SearchParams(**body.model_dump())
    try:
        res = yt.search(db, settings, params)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    videos: list[yt.VideoInfo] = res["videos"]
    ids = [v.youtube_id for v in videos]
    growth = ref_svc.growth_by_youtube_id(db, ids)
    saved = dict(db.execute(
        select(Reference.youtube_id, Reference.id).where(Reference.youtube_id.in_(ids))
    ).all()) if ids else {}
    return RadarResult(
        videos=[
            RadarVideo(
                youtube_id=v.youtube_id, url=v.url, title=v.title, channel_title=v.channel_title,
                published_at=v.published_at, duration_seconds=v.duration_seconds,
                thumbnail_url=v.thumbnail_url, language=v.language, category_id=v.category_id,
                view_count=v.view_count, like_count=v.like_count, comment_count=v.comment_count,
                avg_views_per_day=_avg_per_day(v),
                growth=GrowthOut(**growth[v.youtube_id].__dict__),
                reference_id=saved.get(v.youtube_id),
            )
            for v in videos
        ],
        next_page_token=res["next_page_token"],
        total_results=res["total_results"],
        filtered_out=res["filtered_out"],
    )


@router.post("/radar/save", response_model=list[ReferenceOut], status_code=201)
def save(body: RadarSave, db: Session = Depends(get_db),
         settings: Settings = Depends(get_settings)):
    """Guarda videos del radar en la biblioteca (re-consulta metadatos a YouTube, 1 unidad)."""
    ids = list(dict.fromkeys(body.youtube_ids))
    existing = set(db.scalars(select(Reference.youtube_id).where(Reference.youtube_id.in_(ids))))
    todo = [i for i in ids if i not in existing]
    created: list[Reference] = []
    if todo:
        for v in yt.fetch_videos(db, settings, todo):
            ref = Reference(url=v.url)
            yt.apply_metadata(ref, v, yt.category_title(db, settings, v.category_id))
            if body.category:
                ref.category = body.category
            ref.tags = ref_svc.get_or_create_tags(db, body.tags)
            db.add(ref)
            db.flush()
            created.append(ref)
            yt.record_snapshots(db, [v])
        db.commit()
    return [ReferenceOut.model_validate(r).model_copy(
        update={"growth": GrowthOut(**ref_svc.growth_for(db, r).__dict__)}) for r in created]


@router.post("/references/{ref_id}/refresh", response_model=ReferenceOut)
def refresh(ref_id: int, db: Session = Depends(get_db),
            settings: Settings = Depends(get_settings)):
    """Actualiza metadatos y registra una nueva medición (1 unidad de cuota)."""
    ref = ref_svc.get_reference(db, ref_id)
    if not ref.youtube_id:
        raise HTTPException(422, "Sólo se pueden actualizar referencias de YouTube.")
    videos = yt.fetch_videos(db, settings, [ref.youtube_id])
    if not videos:
        raise HTTPException(404, "YouTube no devolvió el video (¿privado o eliminado?).")
    yt.apply_metadata(ref, videos[0], yt.category_title(db, settings, videos[0].category_id))
    yt.record_snapshots(db, videos)
    db.commit()
    out = ReferenceOut.model_validate(ref)
    out.growth = GrowthOut(**ref_svc.growth_for(db, ref).__dict__)
    return out


@router.get("/references/{ref_id}/snapshots")
def snapshots(ref_id: int, db: Session = Depends(get_db)):
    ref = ref_svc.get_reference(db, ref_id)
    return [
        {"captured_at": s.captured_at, "view_count": s.view_count, "like_count": s.like_count,
         "comment_count": s.comment_count}
        for s in ref_svc.snapshots_for(db, ref)
    ]


@router.post("/references/refresh-metrics", status_code=202)
def refresh_all(db: Session = Depends(get_db)):
    """Encola la actualización de métricas de todas las referencias de YouTube."""
    job = jobs.enqueue(db, "refresh_metrics", {})
    return {"job_id": job.id}
