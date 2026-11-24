# Arquitectura — Viral Clip Factory

## Vista general

```
 Navegador ──► Next.js (frontend, :3000) ──/api/* rewrite──► FastAPI (backend, :8000)
                 sólo UI, sin secretos                        │
                                                              ├─ SQLAlchemy ─► SQLite (→ PostgreSQL)
                                                              ├─ storage/  (uploads, audio, renders)
                                                              ├─ Job runner (hilo worker + tabla jobs)
                                                              │    ├─ Whisper local (transcripción)
                                                              │    ├─ espeak-ng (voz en off)
                                                              │    └─ FFmpeg (render 1080x1920)
                                                              ├─ YouTube Data API v3 (metadatos)
                                                              └─ Anthropic Claude (análisis, guiones)
```

Principio: **el backend es la única frontera hacia el exterior**. El frontend nunca conoce
credenciales ni URLs de proveedores; sólo conoce `BACKEND_URL` del lado servidor de Next.

## Módulos del backend

| Módulo | Responsabilidad | Fase |
|---|---|---|
| `core/config` | Settings desde entorno, flags de proveedor, límites | 1 |
| `db`, `models`, `alembic` | Esquema, sesiones, migraciones | 2 |
| `services/usage` | Contador de uso diario/mensual y costo estimado; bloquea al superar límites | 2 |
| `services/jobs` | Cola persistida de tareas largas (estado, progreso, error) | 2 |
| `services/youtube` | `search.list` + `videos.list`, parseo ISO-8601, snapshots de métricas | 3 |
| `services/library` | Referencias, etiquetas, favoritos, adjuntos autorizados | 4 |
| `services/transcription` | Whisper local con marcas temporales; también acepta subtítulos/texto pegado | 5 |
| `services/analysis` | Claude → informe estructurado (gancho, narrativa, edición, potencial) | 5 |
| `services/scripts` | Claude → 3 guiones originales + control de similitud con la fuente | 6 |
| `services/tts` | Proveedores de voz intercambiables (espeak-ng local por defecto) | 7 |
| `services/render` | Plantillas → grafo FFmpeg (fondos, Ken Burns, subtítulos ASS, mezcla de audio) | 7 |
| `services/workflow` | Máquina de estados editorial y transiciones válidas | 8 |

## Modelo de datos (Fase 2)

- `Reference` — youtube_id (único, nullable para manuales), title, channel, url, thumbnail,
  published_at, duration_s, description, language, category, is_favorite, status, created_at.
- `MetricSnapshot` — reference_id, views, likes, comments, captured_at. Base del cálculo de
  crecimiento (vistas/hora entre snapshots; nunca con un solo punto).
- `Tag` + `reference_tags`.
- `MediaAsset` — archivo adjunto (video/audio/imagen/música), ruta, mime, duración,
  `rights_declaration` (propio / licenciado / dominio público + nota), owner reference opcional.
- `Transcript` — reference_id, source (whisper/manual/subtítulos), language, segments JSON
  (start, end, text).
- `Analysis` — reference_id, report JSON (observed / inferred / recommendations), editorial
  score 0–100, model, tokens, cost.
- `Script` — reference_id, variant (1–3), contenido estructurado JSON, editado por usuario,
  status.
- `Clip` — script_id, template, duration_target (15/30/45/60), brand config, file path,
  status, render log.
- `Job` — type, payload, status, progress, error, timestamps.
- `UsageEvent` — provider, operation, units/tokens, cost_usd, created_at.

### Estados editoriales

```
Reference:  pending_analysis → analyzed → script_generated
Script:     pending_approval → approved_for_production | rejected
Clip:       in_production → pending_review → approved | rejected
```
(Coinciden 1:1 con los 9 estados de la especificación.)

## Motor audiovisual

- **Motor principal: FFmpeg dirigido desde Python.** Determinista, sin dependencias de
  navegador, verificado en este entorno (libx264, aac, libass, zoompan, drawtext).
- Cada plantilla (documental, curiosidades, noticias, historia, cinematográfica, rankings) es
  un objeto Python que define: paleta/tipografía, estilo de subtítulos ASS (karaoke palabra a
  palabra), tratamiento de fondos (Ken Burns, blur-fill para material horizontal), barras/
  rótulos, transiciones (`xfade`) y mezcla de audio (voz + música con ducking).
- Tiempos de subtítulos: de la duración real del audio TTS por segmento (o Whisper sobre la
  voz generada) — no estimados.
- **Remotion (opcional, Fase 7):** `video/` con composiciones React para plantillas con
  animación avanzada, renderizadas con el Chromium del sistema. Se activa sólo si el render
  headless funciona en el entorno y si la licencia aplica (ver costos).

## Seguridad
- Secretos sólo en `.env` del backend (`SecretStr`), nunca serializados.
- CORS restringido a `CORS_ORIGINS`; en uso normal el navegador ni siquiera habla con el backend.
- Uploads: límite de tamaño, validación de MIME con ffprobe, nombres de archivo generados
  (UUID), almacenamiento fuera de rutas servidas estáticamente salvo vía endpoint controlado.
- MVP monousuario y local; autenticación queda fuera de alcance y se documenta como requisito
  antes de exponerlo en red.
