import re
from urllib.parse import parse_qs, urlparse

_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_youtube_id(url_or_id: str) -> str | None:
    """Extrae el ID de 11 caracteres de cualquier formato común de URL de YouTube."""
    s = url_or_id.strip()
    if _ID.match(s):
        return s
    if not re.match(r"^https?://", s):
        s = "https://" + s
    u = urlparse(s)
    host = (u.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    candidate: str | None = None
    if host == "youtu.be":
        candidate = u.path.lstrip("/").split("/")[0]
    elif host in {"youtube.com", "music.youtube.com", "youtube-nocookie.com"}:
        if u.path == "/watch":
            candidate = (parse_qs(u.query).get("v") or [None])[0]
        else:
            parts = [p for p in u.path.split("/") if p]
            if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live", "v", "e"}:
                candidate = parts[1]
    return candidate if candidate and _ID.match(candidate) else None


def canonical_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"
