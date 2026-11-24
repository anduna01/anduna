from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Job
from app.services import jobs

router = APIRouter(tags=["jobs"])


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    status: str
    progress: float
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


@router.get("/jobs", response_model=list[JobOut])
def list_jobs(limit: int = 50, db: Session = Depends(get_db)):
    return list(db.scalars(select(Job).order_by(Job.id.desc()).limit(min(limit, 200))))


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(404, "Job no encontrado")
    return job


@router.post("/system/selftest", response_model=JobOut, status_code=202)
def render_selftest(db: Session = Depends(get_db)):
    """Encola un render de prueba (2 s, 1080x1920, H.264/AAC) para validar FFmpeg."""
    return jobs.enqueue(db, "render_selftest", {})
