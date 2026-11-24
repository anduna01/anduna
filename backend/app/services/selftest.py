"""Job de autodiagnóstico: renderiza un MP4 vertical real y lo valida con ffprobe."""

import json
import subprocess
import uuid

from app.core.config import get_settings
from app.services.jobs import JobContext, register


def probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
        capture_output=True, text=True, timeout=30, check=True,
    )
    return json.loads(out.stdout)


@register("render_selftest")
def render_selftest(ctx: JobContext, payload: dict) -> dict:
    out_dir = get_settings().storage_dir / "selftest"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"selftest-{uuid.uuid4().hex[:8]}.mp4"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30:duration=2",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    ctx.progress(0.8)
    info = probe(str(path))
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next(s for s in info["streams"] if s["codec_type"] == "audio")
    ok = (v["codec_name"], v["width"], v["height"], a["codec_name"]) == ("h264", 1080, 1920, "aac")
    path.unlink(missing_ok=True)
    if not ok:
        raise RuntimeError(f"Salida inesperada: {v['codec_name']} {v['width']}x{v['height']} "
                           f"{a['codec_name']}")
    return {"video": f"{v['codec_name']} {v['width']}x{v['height']}", "audio": a["codec_name"],
            "duration": float(info["format"]["duration"])}
