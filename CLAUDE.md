# CLAUDE.md — Viral Clip Factory

Reglas permanentes del proyecto. Leer antes de cualquier cambio.

## Qué es
Fábrica semiautomática de clips verticales: investiga videos exitosos de YouTube, los analiza
con Claude, genera guiones **originales** inspirados en su estructura, produce clips 9:16 con
FFmpeg y los somete a aprobación humana. Producto real, no demo.

## Estructura
- `backend/` — FastAPI + Pydantic + SQLAlchemy (SQLite en MVP). Toda la lógica y todas las
  llamadas a servicios externos viven aquí.
- `frontend/` — Next.js (App Router) + React + TypeScript + Tailwind. Sólo UI.
  El navegador llama a `/api/*` en Next, que reescribe al backend (`BACKEND_URL`).
- `video/` — (Fase 7) composiciones Remotion opcionales.
- `docs/` — arquitectura, plan, registro de fases (`docs/CHANGELOG.md`).
- `index.html` en la raíz es un proyecto ajeno preexistente (calculadora). No tocarlo.

## Comandos
- `make setup` — instala dependencias backend (uv) y frontend (npm).
- `make backend` / `make frontend` — servidores de desarrollo (8000 / 3000).
- `make test` — pytest + ruff + eslint + tsc. **Debe pasar antes de cada commit.**
- `make build` — build de producción del frontend.

## Reglas no negociables
1. **Nada simulado.** Una funcionalidad sólo se marca terminada si funciona de punta a punta.
   Si una sección no está lista, la UI lo dice explícitamente (`PendingSection`). Prohibido
   devolver datos falsos/mock desde endpoints de producción.
2. **Secretos sólo en variables de entorno del backend.** Nunca en el frontend, nunca en logs,
   nunca en respuestas de API, nunca en git. `.env.example` documenta cada variable.
   Las variables `NEXT_PUBLIC_*` no pueden contener credenciales.
3. **Costos bajo control.** Ninguna acción contrata servicios pagos. Cada llamada a un proveedor
   externo pasa por el control de límites (`limit_*`) y registra costo estimado. Cada proveedor
   se puede desactivar (`*_ENABLED=false`) y el sistema debe degradar con un mensaje claro.
4. **Mínimo envío a terceros.** A Claude se le envía texto (transcripción + metadatos), no
   archivos de video. No subir medios a servicios externos salvo que el usuario lo configure.
5. **Derechos.** No descargar automáticamente material de YouTube. Sólo se procesan archivos
   que el usuario adjunta declarando que son propios o autorizados. Música e imágenes de
   producción: sólo de la biblioteca de assets del usuario o generadas localmente.
6. **Originalidad.** Los guiones toman la referencia como inspiración estructural. El prompt y
   un control posterior deben evitar copiar frases, guiones o secuencias distintivas.
7. **Honestidad analítica.** El puntaje es "potencial editorial", nunca probabilidad de
   viralización. Los informes separan *observado* / *inferido* / *recomendado*. No afirmar
   crecimiento con una sola medición: requiere ≥2 snapshots históricos.
8. **Control humano.** Nunca publicar automáticamente. Las transiciones de estado editoriales
   (aprobar/rechazar guion o clip) son acciones explícitas del usuario.

## Convenciones
- Idioma de UI, docs y mensajes: español. Identificadores de código: inglés.
- Backend: rutas en `app/api/routes/`, lógica en `app/services/`, modelos ORM en `app/models/`,
  esquemas Pydantic en `app/schemas/`. Config sólo vía `app.core.config.get_settings()`.
- Migraciones con Alembic; no usar `create_all` fuera de tests.
- Claude: SDK oficial `anthropic`, modelo por `ANTHROPIC_MODEL` (default `claude-opus-5-5`),
  salidas estructuradas validadas con Pydantic. Registrar tokens de `response.usage`.
- Tareas largas (transcripción, render) corren como *jobs* persistidos con estado consultable;
  nunca bloquear un request HTTP.
- Formato de salida de clips: MP4, H.264 (yuv420p), AAC, 1080x1920, 30 fps, `+faststart`.
- Tests: cada fase agrega tests de su funcionalidad. Tests no llaman a APIs pagas reales
  (usar fakes inyectados); las pruebas reales con claves se documentan como manuales.

## Metodología
Trabajo por fases (ver `docs/PLAN.md`). Al cerrar cada fase: tests en verde, verificación
manual de punta a punta, entrada en `docs/CHANGELOG.md` con lo terminado y lo pendiente.
No avanzar de fase sin verificar la anterior.
