"""Estados editoriales. Juntos cubren los 9 estados de la especificación."""

from enum import StrEnum


class ReferenceStatus(StrEnum):
    pending_analysis = "pending_analysis"  # Pendiente de análisis
    analyzed = "analyzed"  # Analizado
    script_generated = "script_generated"  # Guion generado


class ScriptStatus(StrEnum):
    pending_approval = "pending_approval"  # Pendiente de aprobación
    approved_for_production = "approved_for_production"  # Aprobado para producción
    rejected = "rejected"


class ClipStatus(StrEnum):
    in_production = "in_production"  # En producción
    pending_review = "pending_review"  # Pendiente de revisión
    approved = "approved"  # Aprobado
    rejected = "rejected"  # Rechazado
    failed = "failed"  # Error técnico de render (no editorial)


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
