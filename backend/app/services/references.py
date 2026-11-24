from collections import defaultdict

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import MetricSnapshot, Reference, Tag
from app.services.metrics import Growth, compute_growth
from app.services.youtube_urls import canonical_url, extract_youtube_id


class DuplicateReference(Exception):
    def __init__(self, existing: Reference):
        super().__init__(f"La referencia ya existe (id {existing.id}).")
        self.existing = existing


def normalize_tag(name: str) -> str:
    return " ".join(name.strip().lower().split())[:64]


def get_or_create_tags(db: Session, names: list[str]) -> list[Tag]:
    clean = sorted({normalize_tag(n) for n in names if normalize_tag(n)})
    if not clean:
        return []
    existing = {t.name: t for t in db.scalars(select(Tag).where(Tag.name.in_(clean)))}
    tags = []
    for n in clean:
        t = existing.get(n)
        if t is None:
            t = Tag(name=n)
            db.add(t)
        tags.append(t)
    return tags


def get_reference(db: Session, ref_id: int) -> Reference:
    ref = db.get(Reference, ref_id)
    if ref is None:
        raise NotFound(f"Referencia {ref_id} no encontrada")
    return ref


def create_from_url(
    db: Session, url: str, title: str | None, category: str | None, tags: list[str],
    notes: str | None,
) -> Reference:
    """Alta manual por URL. Si es YouTube se normaliza el ID (los metadatos se completan con
    la API cuando está configurada). Otras URLs se guardan como referencia manual."""
    yt_id = extract_youtube_id(url)
    if yt_id:
        dup = db.scalar(select(Reference).where(Reference.youtube_id == yt_id))
        if dup:
            raise DuplicateReference(dup)
        ref = Reference(source="youtube", youtube_id=yt_id, url=canonical_url(yt_id),
                        thumbnail_url=f"https://i.ytimg.com/vi/{yt_id}/hqdefault.jpg")
    else:
        if not url.startswith(("http://", "https://")):
            raise ValueError("La URL debe comenzar con http:// o https://")
        dup = db.scalar(select(Reference).where(Reference.url == url))
        if dup:
            raise DuplicateReference(dup)
        ref = Reference(source="manual", url=url)
    ref.title = (title or "").strip() or (f"YouTube {yt_id}" if yt_id else url)
    ref.category = category
    ref.notes = notes
    ref.tags = get_or_create_tags(db, tags)
    db.add(ref)
    db.commit()
    return ref


def update_reference(db: Session, ref: Reference, data: dict) -> Reference:
    tags = data.pop("tags", None)
    for k, v in data.items():
        setattr(ref, k, v)
    if tags is not None:
        ref.tags = get_or_create_tags(db, tags)
    db.commit()
    return ref


def list_references(
    db: Session, *, q: str | None = None, status: str | None = None, category: str | None = None,
    tag: str | None = None, favorite: bool | None = None, sort: str = "-created_at",
    limit: int = 50, offset: int = 0,
) -> tuple[list[Reference], int]:
    stmt = select(Reference)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Reference.title.ilike(like), Reference.channel_title.ilike(like),
                              Reference.description.ilike(like), Reference.notes.ilike(like)))
    if status:
        stmt = stmt.where(Reference.status == status)
    if category:
        stmt = stmt.where(Reference.category == category)
    if favorite is not None:
        stmt = stmt.where(Reference.is_favorite == favorite)
    if tag:
        stmt = stmt.where(Reference.tags.any(Tag.name == normalize_tag(tag)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    sort_map = {
        "created_at": Reference.created_at, "views": Reference.view_count,
        "published_at": Reference.published_at, "title": Reference.title,
    }
    desc = sort.startswith("-")
    col = sort_map.get(sort.lstrip("-"), Reference.created_at)
    order = col.desc().nulls_last() if desc else col.asc().nulls_last()
    stmt = stmt.order_by(order, Reference.id.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt)), total


def growth_by_youtube_id(db: Session, youtube_ids: list[str]) -> dict[str, Growth]:
    points: dict[str, list] = defaultdict(list)
    if youtube_ids:
        rows = db.execute(
            select(MetricSnapshot.youtube_id, MetricSnapshot.captured_at, MetricSnapshot.view_count)
            .where(MetricSnapshot.youtube_id.in_(youtube_ids))
        ).all()
        for yid, t, v in rows:
            points[yid].append((t, v))
    return {yid: compute_growth(points.get(yid, [])) for yid in youtube_ids}


def growth_for(db: Session, ref: Reference) -> Growth:
    if not ref.youtube_id:
        return compute_growth([])
    return growth_by_youtube_id(db, [ref.youtube_id])[ref.youtube_id]


def snapshots_for(db: Session, ref: Reference) -> list[MetricSnapshot]:
    if not ref.youtube_id:
        return []
    return list(db.scalars(
        select(MetricSnapshot).where(MetricSnapshot.youtube_id == ref.youtube_id)
        .order_by(MetricSnapshot.captured_at)
    ))
