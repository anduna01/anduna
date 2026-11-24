"""Modelos ORM. Importar todo aquí para que Alembic los detecte."""

from app.models.entities import (
    Analysis,
    Clip,
    Job,
    MediaAsset,
    MetricSnapshot,
    Reference,
    Script,
    Tag,
    Transcript,
    UsageEvent,
    reference_tags,
)
from app.models.enums import ClipStatus, JobStatus, ReferenceStatus, ScriptStatus

__all__ = [
    "Analysis", "Clip", "Job", "MediaAsset", "MetricSnapshot", "Reference", "Script", "Tag",
    "Transcript", "UsageEvent", "reference_tags",
    "ClipStatus", "JobStatus", "ReferenceStatus", "ScriptStatus",
]
