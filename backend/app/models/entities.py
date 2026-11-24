from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.types import UTCDateTime
from app.models.enums import ClipStatus, JobStatus, ReferenceStatus, ScriptStatus


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, onupdate=utcnow)


reference_tags = Table(
    "reference_tags",
    Base.metadata,
    Column("reference_id", ForeignKey("references.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)


class Reference(TimestampMixin, Base):
    __tablename__ = "references"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(16), default="youtube")  # youtube | manual
    youtube_id: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    channel_title: Mapped[str | None] = mapped_column(String(255))
    channel_id: Mapped[str | None] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(1000))
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000))
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(16))
    region: Mapped[str | None] = mapped_column(String(8))
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    category_id: Mapped[str | None] = mapped_column(String(8))
    view_count: Mapped[int | None] = mapped_column(Integer)
    like_count: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    last_fetched_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(32), default=ReferenceStatus.pending_analysis, index=True
    )

    tags: Mapped[list[Tag]] = relationship(secondary=reference_tags, lazy="selectin")
    snapshots: Mapped[list["MetricSnapshot"]] = relationship(
        back_populates="reference",
        cascade="all, delete-orphan",
        order_by="MetricSnapshot.captured_at",
    )
    assets: Mapped[list["MediaAsset"]] = relationship(back_populates="reference")
    transcripts: Mapped[list["Transcript"]] = relationship(
        back_populates="reference", cascade="all, delete-orphan"
    )
    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="reference", cascade="all, delete-orphan"
    )
    scripts: Mapped[list["Script"]] = relationship(
        back_populates="reference", cascade="all, delete-orphan"
    )


class MetricSnapshot(Base):
    """Medición histórica de métricas públicas. Base para calcular crecimiento."""

    __tablename__ = "metric_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[int] = mapped_column(
        ForeignKey("references.id", ondelete="CASCADE"), index=True
    )
    view_count: Mapped[int | None] = mapped_column(Integer)
    like_count: Mapped[int | None] = mapped_column(Integer)
    comment_count: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow)
    reference: Mapped[Reference] = relationship(back_populates="snapshots")


class MediaAsset(TimestampMixin, Base):
    """Archivo propio o autorizado (video, audio, imagen, música, subtítulos)."""

    __tablename__ = "media_assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[int | None] = mapped_column(
        ForeignKey("references.id", ondelete="SET NULL"), index=True
    )
    kind: Mapped[str] = mapped_column(String(16))  # video | audio | image | music | subtitle
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(1000))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    rights_type: Mapped[str] = mapped_column(String(32))  # own | licensed | public_domain | cc
    rights_note: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[Reference | None] = relationship(back_populates="assets")


class Transcript(TimestampMixin, Base):
    __tablename__ = "transcripts"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[int] = mapped_column(
        ForeignKey("references.id", ondelete="CASCADE"), index=True
    )
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(16))  # whisper | subtitle_file | manual
    language: Mapped[str | None] = mapped_column(String(16))
    text: Mapped[str] = mapped_column(Text)
    segments: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    reference: Mapped[Reference] = relationship(back_populates="transcripts")


class Analysis(TimestampMixin, Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[int] = mapped_column(
        ForeignKey("references.id", ondelete="CASCADE"), index=True
    )
    transcript_id: Mapped[int | None] = mapped_column(
        ForeignKey("transcripts.id", ondelete="SET NULL")
    )
    report: Mapped[dict[str, Any]] = mapped_column(JSON)
    editorial_score: Mapped[int] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    reference: Mapped[Reference] = relationship(back_populates="analyses")


class Script(TimestampMixin, Base):
    __tablename__ = "scripts"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference_id: Mapped[int] = mapped_column(
        ForeignKey("references.id", ondelete="CASCADE"), index=True
    )
    analysis_id: Mapped[int | None] = mapped_column(ForeignKey("analyses.id", ondelete="SET NULL"))
    variant: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    similarity_score: Mapped[float | None] = mapped_column(Float)
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ScriptStatus.pending_approval, index=True
    )
    reference: Mapped[Reference] = relationship(back_populates="scripts")
    clips: Mapped[list["Clip"]] = relationship(
        back_populates="script", cascade="all, delete-orphan"
    )


class Clip(TimestampMixin, Base):
    __tablename__ = "clips"
    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id", ondelete="CASCADE"), index=True)
    template: Mapped[str] = mapped_column(String(32))
    target_duration: Mapped[int] = mapped_column(Integer)  # 15 | 30 | 45 | 60
    options: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    file_path: Mapped[str | None] = mapped_column(String(1000))
    actual_duration: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default=ClipStatus.in_production, index=True)
    review_note: Mapped[str | None] = mapped_column(Text)
    render_log: Mapped[str | None] = mapped_column(Text)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    script: Mapped[Script] = relationship(back_populates="clips")


class Job(TimestampMixin, Base):
    """Tarea larga persistida (transcripción, render...). Se consulta por polling."""

    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(32), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default=JobStatus.queued, index=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime())


class UsageEvent(Base):
    """Registro de uso de proveedores externos y costo estimado."""

    __tablename__ = "usage_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)  # anthropic | youtube | render
    operation: Mapped[str] = mapped_column(String(64))
    units: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utcnow, index=True)
