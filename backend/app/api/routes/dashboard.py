from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import Analysis, Clip, ClipStatus, Reference, Script
from app.services import usage

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    def count(stmt) -> int:
        return db.scalar(stmt) or 0

    return {
        "references": count(select(func.count(Reference.id))),
        "analyzed": count(select(func.count(func.distinct(Analysis.reference_id)))),
        "scripts": count(select(func.count(Script.id))),
        "clips_produced": count(
            select(func.count(Clip.id)).where(Clip.status.not_in(
                [ClipStatus.in_production, ClipStatus.failed]))
        ),
        "clips_pending_review": count(
            select(func.count(Clip.id)).where(Clip.status == ClipStatus.pending_review)
        ),
        "clips_approved": count(
            select(func.count(Clip.id)).where(Clip.status == ClipStatus.approved)
        ),
        "usage": usage.summary(db, settings),
    }
