"""Servidor HTTP falso de YouTube para pruebas E2E manuales de la UI (NO es producción).

Uso: YOUTUBE_API_BASE=http://127.0.0.1:8765/youtube/v3 YOUTUBE_API_KEY=test-key
     python -m uvicorn tests.fake_youtube_server:app --port 8765
"""

import httpx
from fastapi import FastAPI, Request, Response

from tests.fake_youtube import FakeYouTube, video_item

fake = FakeYouTube()
_seed = [
    ("aaaaaaaaaa1", 2_400_000, "PT58S", 5, "El misterio del faro abandonado"),
    ("aaaaaaaaaa2", 890_000, "PT41S", 12, "3 datos que nadie te contó sobre Roma"),
    ("aaaaaaaaaa3", 5_100_000, "PT12M4S", 20, "La historia completa de Atlantis"),
    ("aaaaaaaaaa4", 310_000, "PT33S", 2, "¿Por qué el cielo es azul?"),
]
for vid, views, dur, days, title in _seed:
    fake.videos[vid] = video_item(vid, views, dur, days, title=title)
fake.search_results = list(fake.videos)

app = FastAPI()


@app.get("/youtube/v3/{path}")
def proxy(path: str, request: Request) -> Response:
    req = httpx.Request("GET", str(request.url), headers=dict(request.headers))
    res = fake.handler(req)
    return Response(content=res.content, status_code=res.status_code,
                    media_type="application/json")
