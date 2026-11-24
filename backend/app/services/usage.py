"""Control de uso y costos de proveedores externos.

Toda operación paga o con cuota debe llamar a `ensure_allowed` antes y a `record` después.
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ProviderDisabled, UsageLimitExceeded
from app.models import UsageEvent

# Costos en unidades de cuota de YouTube Data API v3.
YOUTUBE_UNIT_COST = {"search.list": 100, "videos.list": 1, "videoCategories.list": 1}


def _start_of_day() -> datetime:
    now = datetime.now(UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _start_of_month() -> datetime:
    return _start_of_day().replace(day=1)


def anthropic_cost(settings: Settings, input_tokens: int, output_tokens: int) -> float:
    return round(
        input_tokens / 1e6 * settings.anthropic_input_usd_per_mtok
        + output_tokens / 1e6 * settings.anthropic_output_usd_per_mtok,
        6,
    )


def _count_today(db: Session, provider: str) -> int:
    return db.scalar(
        select(func.count(UsageEvent.id)).where(
            UsageEvent.provider == provider, UsageEvent.created_at >= _start_of_day()
        )
    ) or 0


def youtube_units_today(db: Session) -> int:
    return db.scalar(
        select(func.coalesce(func.sum(UsageEvent.units), 0)).where(
            UsageEvent.provider == "youtube", UsageEvent.created_at >= _start_of_day()
        )
    ) or 0


def month_cost(db: Session) -> float:
    return float(
        db.scalar(
            select(func.coalesce(func.sum(UsageEvent.cost_usd), 0.0)).where(
                UsageEvent.created_at >= _start_of_month()
            )
        )
        or 0.0
    )


def ensure_allowed(db: Session, settings: Settings, provider: str, units: int = 0) -> None:
    """Lanza ProviderDisabled / UsageLimitExceeded si la operación no está permitida."""
    if provider == "anthropic":
        if not settings.anthropic_enabled:
            raise ProviderDisabled("Claude está desactivado (ANTHROPIC_ENABLED=false).")
        if not settings.anthropic_configured:
            raise ProviderDisabled("Falta ANTHROPIC_API_KEY en el entorno del backend.")
        if _count_today(db, "anthropic") >= settings.limit_claude_calls_per_day:
            raise UsageLimitExceeded(
                "Límite diario de llamadas a Claude alcanzado "
                f"({settings.limit_claude_calls_per_day})."
            )
        if month_cost(db) >= settings.limit_monthly_budget_usd:
            raise UsageLimitExceeded(
                f"Presupuesto mensual agotado (USD {settings.limit_monthly_budget_usd:.2f})."
            )
    elif provider == "youtube":
        if not settings.youtube_enabled:
            raise ProviderDisabled("YouTube está desactivado (YOUTUBE_ENABLED=false).")
        if not settings.youtube_configured:
            raise ProviderDisabled("Falta YOUTUBE_API_KEY en el entorno del backend.")
        used = youtube_units_today(db)
        if used + units > settings.limit_youtube_units_per_day:
            raise UsageLimitExceeded(
                f"Cuota diaria de YouTube insuficiente: usadas {used}, se requieren {units}, "
                f"límite {settings.limit_youtube_units_per_day}."
            )
    elif provider == "render":
        if _count_today(db, "render") >= settings.limit_renders_per_day:
            raise UsageLimitExceeded(
                f"Límite diario de renders alcanzado ({settings.limit_renders_per_day})."
            )


def record(
    db: Session,
    provider: str,
    operation: str,
    *,
    units: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
    meta: dict | None = None,
) -> UsageEvent:
    ev = UsageEvent(
        provider=provider,
        operation=operation,
        units=units,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        meta=meta or {},
    )
    db.add(ev)
    db.commit()
    return ev


def summary(db: Session, settings: Settings) -> dict:
    return {
        "claude_calls_today": _count_today(db, "anthropic"),
        "claude_calls_limit": settings.limit_claude_calls_per_day,
        "youtube_units_today": youtube_units_today(db),
        "youtube_units_limit": settings.limit_youtube_units_per_day,
        "renders_today": _count_today(db, "render"),
        "renders_limit": settings.limit_renders_per_day,
        "month_cost_usd": round(month_cost(db), 4),
        "monthly_budget_usd": settings.limit_monthly_budget_usd,
    }
