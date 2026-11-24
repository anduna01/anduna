from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.services.system_check import collect_status

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/system/status")
def system_status(settings: Settings = Depends(get_settings)) -> dict:
    """Estado de herramientas/proveedores y límites. Nunca devuelve credenciales."""
    return {
        "app": settings.app_name,
        "env": settings.app_env,
        "components": [c.as_dict() for c in collect_status(settings)],
        "limits": {
            "claude_calls_per_day": settings.limit_claude_calls_per_day,
            "youtube_units_per_day": settings.limit_youtube_units_per_day,
            "monthly_budget_usd": settings.limit_monthly_budget_usd,
            "upload_mb": settings.limit_upload_mb,
            "renders_per_day": settings.limit_renders_per_day,
        },
    }
