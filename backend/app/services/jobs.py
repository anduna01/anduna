"""Cola de tareas largas persistida en la base de datos.

Un hilo worker toma jobs `queued` y ejecuta el handler registrado para su tipo.
Simple y suficiente para el MVP monousuario; reemplazable por RQ/Celery sin cambiar la API.
"""

import logging
import threading
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Job, JobStatus

log = logging.getLogger(__name__)


class JobContext:
    """Se pasa a cada handler para reportar progreso."""

    def __init__(self, db: Session, job: Job):
        self.db = db
        self.job = job

    def progress(self, value: float) -> None:
        self.job.progress = max(0.0, min(1.0, value))
        self.db.commit()


Handler = Callable[[JobContext, dict[str, Any]], dict[str, Any] | None]
_HANDLERS: dict[str, Handler] = {}


def register(job_type: str) -> Callable[[Handler], Handler]:
    def deco(fn: Handler) -> Handler:
        _HANDLERS[job_type] = fn
        return fn

    return deco


def enqueue(db: Session, job_type: str, payload: dict[str, Any]) -> Job:
    if job_type not in _HANDLERS:
        raise ValueError(f"Tipo de job desconocido: {job_type}")
    job = Job(type=job_type, payload=payload)
    db.add(job)
    db.commit()
    _wake.set()
    return job


def _claim_next(db: Session) -> Job | None:
    job_id = db.scalar(
        select(Job.id).where(Job.status == JobStatus.queued).order_by(Job.id).limit(1)
    )
    if job_id is None:
        return None
    # Reclamo atómico: sólo un worker gana la transición queued -> running.
    res = db.execute(
        update(Job)
        .where(Job.id == job_id, Job.status == JobStatus.queued)
        .values(status=JobStatus.running, started_at=datetime.now(UTC))
    )
    db.commit()
    if res.rowcount != 1:
        return None
    return db.get(Job, job_id)


def run_job(db: Session, job: Job) -> None:
    handler = _HANDLERS.get(job.type)
    try:
        if handler is None:
            raise RuntimeError(f"Sin handler para '{job.type}'")
        result = handler(JobContext(db, job), dict(job.payload or {}))
        job.status = JobStatus.succeeded
        job.result = result or {}
        job.progress = 1.0
    except Exception as exc:  # noqa: BLE001 - se persiste el error para el usuario
        db.rollback()
        log.exception("Job %s falló", job.id)
        job = db.get(Job, job.id)
        job.status = JobStatus.failed
        job.error = f"{type(exc).__name__}: {exc}"
        job.result = {"traceback": traceback.format_exc(limit=5)}
    job.finished_at = datetime.now(UTC)
    db.commit()


def run_pending_once() -> int:
    """Procesa todos los jobs en cola de forma síncrona (útil en tests y CLI)."""
    count = 0
    with SessionLocal() as db:
        while (job := _claim_next(db)) is not None:
            run_job(db, job)
            count += 1
    return count


def recover_interrupted() -> None:
    """Jobs que quedaron 'running' por un reinicio se marcan como fallidos."""
    with SessionLocal() as db:
        db.execute(
            update(Job)
            .where(Job.status == JobStatus.running)
            .values(status=JobStatus.failed, error="Interrumpido por reinicio del servidor",
                    finished_at=datetime.now(UTC))
        )
        db.commit()


_wake = threading.Event()
_stop = threading.Event()
_thread: threading.Thread | None = None


def _loop() -> None:
    while not _stop.is_set():
        try:
            run_pending_once()
        except Exception:  # noqa: BLE001
            log.exception("Error en el worker de jobs")
        _wake.wait(timeout=2.0)
        _wake.clear()


def start_worker() -> None:
    global _thread
    if _thread and _thread.is_alive():
        return
    recover_interrupted()
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="vcf-job-worker", daemon=True)
    _thread.start()


def stop_worker() -> None:
    _stop.set()
    _wake.set()
    if _thread:
        _thread.join(timeout=5)
