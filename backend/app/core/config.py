"""Configuración central. Todas las credenciales provienen de variables de entorno.

Nunca exponer estos valores al frontend: el endpoint /api/system/status solo informa
si un proveedor está *configurado*, jamás el valor de la clave.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_DIR / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Aplicación ---
    app_env: str = "development"
    app_name: str = "Viral Clip Factory"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Persistencia ---
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'data' / 'vcf.db').as_posix()}"
    storage_dir: Path = BACKEND_DIR / "storage"
    jobs_worker_enabled: bool = True

    # --- Anthropic Claude ---
    anthropic_enabled: bool = True
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: str = "medium"
    # Precios USD por millón de tokens (para estimar costos; actualizar si cambian).
    anthropic_input_usd_per_mtok: float = 4.0
    anthropic_output_usd_per_mtok: float = 20.0

    # --- YouTube Data API v3 ---
    youtube_enabled: bool = True
    youtube_api_key: SecretStr | None = None
    # Sólo para pruebas locales contra un servidor falso; en uso normal no se cambia.
    youtube_api_base: str = "https://www.googleapis.com/youtube/v3"

    # --- Transcripción (Whisper local) ---
    whisper_enabled: bool = True
    whisper_model: str = "base"

    # --- Voz en off ---
    tts_provider: str = "espeak"  # espeak | none

    # --- Límites de uso y costos ---
    limit_claude_calls_per_day: int = 50
    limit_youtube_units_per_day: int = 8000  # cuota gratuita estándar: 10.000 unidades/día
    limit_monthly_budget_usd: float = 20.0
    limit_upload_mb: int = 500
    limit_renders_per_day: int = 30

    @property
    def anthropic_configured(self) -> bool:
        return bool(self.anthropic_api_key and self.anthropic_api_key.get_secret_value())

    @property
    def youtube_configured(self) -> bool:
        return bool(self.youtube_api_key and self.youtube_api_key.get_secret_value())


@lru_cache
def get_settings() -> Settings:
    return Settings()
