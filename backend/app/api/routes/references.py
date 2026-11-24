from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ProviderDisabled, UsageLimitExceeded
from app.db.session import get_db
from app.models import ReferenceStatus, Tag
from app.schemas.references import (
    GrowthOut,
    ReferenceCreateFromUrl,
    ReferenceOut,
    ReferencePage,
    ReferenceUpdate,
    TagOut,
)
from app.services import references as svc
from app.services import youtube as yt

router = APIRouter(tags=["references"])


def _out(db: Session, ref) -> ReferenceOut:
    out = ReferenceOut.model_validate(ref)
    out.growth = GrowthOut(**svc.growth_for(db, ref).__dict__)
    return out


@router.get("/references", response_model=ReferencePage)
def list_references(
    q: str | None = None,
    status: ReferenceStatus | None = None,
    category: str | None = None,
    tag: str | None = None,
    favorite: bool | None = None,
    sort: str = Query("-created_at", pattern=r"^-?(created_at|views|published_at|title)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = svc.list_references(
        db, q=q, status=status, category=category, tag=tag, favorite=favorite, sort=sort,
        limit=limit, offset=offset,
    )
    return ReferencePage(items=[_out(db, r) for r in items], total=total, limit=limit,
                         offset=offset)


@router.post("/references", response_model=ReferenceOut, status_code=201)
def create_reference(body: ReferenceCreateFromUrl, db: Session = Depends(get_db),
                     settings: Settings = Depends(get_settings)):
    try:
        ref = svc.create_from_url(db, body.url, body.title, body.category, body.tags, body.notes)
    except svc.DuplicateReference as e:
        raise HTTPException(409, detail={"message": str(e), "id": e.existing.id}) from e
    except ValueError as e:
        raise HTTPException(422, detail=str(e)) from e
    # Enriquecimiento best-effort: si YouTube no está disponible, la referencia queda igual
    # guardada y puede actualizarse luego con POST /references/{id}/refresh.
    if ref.youtube_id and settings.youtube_enabled and settings.youtube_configured:
        try:
            videos = yt.fetch_videos(db, settings, [ref.youtube_id])
            if videos:
                yt.apply_metadata(ref, videos[0])
                if body.title:
                    ref.title = body.title
                yt.record_snapshots(db, videos)
                db.commit()
        except (yt.YouTubeError, UsageLimitExceeded, ProviderDisabled):
            db.rollback()
    return _out(db, ref)


@router.get("/references/{ref_id}", response_model=ReferenceOut)
def get_reference(ref_id: int, db: Session = Depends(get_db)):
    return _out(db, svc.get_reference(db, ref_id))


@router.patch("/references/{ref_id}", response_model=ReferenceOut)
def update_reference(ref_id: int, body: ReferenceUpdate, db: Session = Depends(get_db)):
    ref = svc.get_reference(db, ref_id)
    return _out(db, svc.update_reference(db, ref, body.model_dump(exclude_unset=True)))


@router.delete("/references/{ref_id}", status_code=204)
def delete_reference(ref_id: int, db: Session = Depends(get_db)):
    ref = svc.get_reference(db, ref_id)
    db.delete(ref)
    db.commit()
    return Response(status_code=204)


@router.get("/tags", response_model=list[TagOut])
def list_tags(db: Session = Depends(get_db)):
    return list(db.scalars(select(Tag).order_by(Tag.name)))
