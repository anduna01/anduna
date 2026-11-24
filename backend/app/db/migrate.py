from alembic.config import Config

from alembic import command
from app.core.config import BACKEND_DIR, get_settings
from app.db.session import engine


def upgrade_to_head() -> None:
    """Aplica migraciones pendientes al arrancar (MVP local)."""
    get_settings()  # asegura que la configuración es válida
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    with engine.begin() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")
