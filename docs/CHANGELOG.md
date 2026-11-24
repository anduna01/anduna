# Registro de fases

## Fase 2 — Base de datos y backend ✅

**Terminado y verificado**
- Modelos SQLAlchemy 2.0: `Reference`, `MetricSnapshot`, `Tag`, `MediaAsset`, `Transcript`,
  `Analysis`, `Script`, `Clip`, `Job`, `UsageEvent`. Estados editoriales como enums (cubren
  los 9 de la especificación). Fechas siempre UTC (`UTCDateTime`, SQLite pierde el tzinfo).
- Alembic con migración inicial; se aplica automáticamente al arrancar (`render_as_batch`
  para SQLite, portable a PostgreSQL).
- API de referencias: alta por URL (normaliza cualquier formato de URL de YouTube, acepta
  URLs no-YouTube como referencia manual, detecta duplicados con 409), listado con búsqueda
  de texto, filtros por estado/categoría/etiqueta/favorito, orden y paginación, edición,
  borrado, etiquetas normalizadas.
- Crecimiento: `compute_growth` sólo reporta con ≥2 snapshots (`sufficient_data`).
- Control de uso y costos: `ensure_allowed` / `record` por proveedor; límites diarios de
  Claude, cuota de YouTube por unidades, renders y presupuesto mensual. Errores → HTTP 429
  (límite) / 503 (proveedor desactivado o sin clave).
- Cola de jobs persistida con hilo worker, reclamo atómico, progreso, errores guardados y
  recuperación de jobs interrumpidos.
- Job real `render_selftest`: MP4 1080x1920 H.264/AAC validado con ffprobe.
- Frontend: Dashboard con los 6 contadores reales y medidores de uso/costos; botón de
  autodiagnóstico de render en Configuración.

**Verificación**
- `pytest`: 22 tests OK (URLs, CRUD, filtros, duplicados, dashboard, crecimiento, costos,
  límites, proveedores desactivados, jobs OK/fallidos, render real).
- `ruff`, `eslint`, `tsc`, `next build`: OK.
- E2E manual: base nueva → migración al arranque → alta de referencia vía proxy Next →
  Dashboard muestra 1 referencia → autodiagnóstico desde el navegador "h264 1080x1920 · aac".

## Fase 1 — Arquitectura y configuración ✅

**Terminado y verificado**
- Relevamiento del entorno, arquitectura (`docs/ARCHITECTURE.md`), plan, costos y riesgos
  (`docs/PLAN.md`), reglas permanentes (`CLAUDE.md`).
- Backend FastAPI: configuración por entorno con `SecretStr`, flags para desactivar
  proveedores, límites de uso, motor SQLAlchemy (SQLite con WAL y FKs), endpoints
  `/api/health` y `/api/system/status` (diagnóstico real de FFmpeg+codecs, Whisper, TTS y
  proveedores, sin exponer credenciales).
- Frontend Next.js 15 + Tailwind 4: layout con las 9 secciones, proxy `/api/*` → backend
  (`BACKEND_URL` sólo del lado servidor), Dashboard y Configuración con estado real; el resto
  de secciones indica explícitamente la fase en que se habilita.
- `.env.example`, `.gitignore`, `Makefile`.

**Verificación**
- `pytest`: 5 tests OK (incluye test de que la clave nunca aparece en la respuesta).
- `ruff`, `eslint`, `tsc --noEmit`, `next build`: OK.
- Arranque real de ambos servidores; proxy `/api/system/status` vía Next OK; Playwright
  renderiza Dashboard sin errores de página.

**Pendiente / detectado**
- Whisper y espeak-ng no instalados (Fases 5 y 7). Descarga de pesos Whisper bloqueada por la
  red de este entorno.
- Claves de Anthropic y YouTube no configuradas.
