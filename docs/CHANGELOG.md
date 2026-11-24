# Registro de fases

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
