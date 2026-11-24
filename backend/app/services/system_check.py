"""Diagnóstico de herramientas locales y proveedores externos (sin exponer secretos)."""

import importlib.util
import shutil
import subprocess
from dataclasses import asdict, dataclass

from app.core.config import Settings


@dataclass
class ComponentStatus:
    name: str
    kind: str  # "tool" | "provider"
    available: bool
    enabled: bool
    detail: str

    def as_dict(self) -> dict:
        return asdict(self)


def _version(cmd: list[str]) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    line = (out.stdout or out.stderr).splitlines()
    return line[0].strip() if line else None


def check_ffmpeg() -> ComponentStatus:
    path = shutil.which("ffmpeg")
    if not path:
        return ComponentStatus("ffmpeg", "tool", False, True, "ffmpeg no encontrado en PATH")
    encoders = _version(["ffmpeg", "-hide_banner", "-encoders"]) is not None
    try:
        enc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True, timeout=5
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        enc = ""
    has_h264 = "libx264" in enc
    has_aac = " aac " in enc
    ok = bool(encoders and has_h264 and has_aac)
    detail = _version(["ffmpeg", "-version"]) or "ffmpeg"
    if not ok:
        detail += " (faltan codificadores libx264/aac)"
    return ComponentStatus("ffmpeg", "tool", ok, True, detail)


def check_python_module(module: str, label: str, enabled: bool) -> ComponentStatus:
    found = importlib.util.find_spec(module) is not None
    return ComponentStatus(
        label, "tool", found, enabled, "instalado" if found else f"módulo '{module}' no instalado"
    )


def check_tts(settings: Settings) -> ComponentStatus:
    if settings.tts_provider == "none":
        return ComponentStatus("tts", "tool", False, False, "voz en off desactivada")
    binary = shutil.which("espeak-ng") or shutil.which("espeak")
    return ComponentStatus(
        "tts",
        "tool",
        bool(binary),
        True,
        f"{settings.tts_provider}: {binary}" if binary else "espeak-ng no instalado",
    )


def collect_status(settings: Settings) -> list[ComponentStatus]:
    return [
        check_ffmpeg(),
        check_python_module("whisper", "whisper", settings.whisper_enabled),
        check_tts(settings),
        ComponentStatus(
            "anthropic",
            "provider",
            settings.anthropic_configured,
            settings.anthropic_enabled,
            f"modelo {settings.anthropic_model}"
            if settings.anthropic_configured
            else "ANTHROPIC_API_KEY no configurada",
        ),
        ComponentStatus(
            "youtube",
            "provider",
            settings.youtube_configured,
            settings.youtube_enabled,
            "YouTube Data API v3"
            if settings.youtube_configured
            else "YOUTUBE_API_KEY no configurada",
        ),
    ]
