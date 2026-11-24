# Plan de implementación, dependencias, costos y riesgos

## 1. Entorno relevado (2026-11-24)

| Herramienta | Versión | Estado |
|---|---|---|
| Python | 3.13 | OK (uv 0.11 para entornos) |
| Node / npm / pnpm | 22 / 10.9 / 10.28 | OK |
| FFmpeg / ffprobe | 6.1.1 | OK: libx264, aac, libass, drawtext, zoompan |
| Chromium + Playwright | preinstalados | OK (verificación de UI; posible motor Remotion) |
| Whisper | — | No instalado; **descarga de pesos bloqueada** por la red del entorno |
| espeak-ng (TTS) | — | No instalado (se instala vía apt en Fase 7) |
| Claves Anthropic / YouTube | — | No configuradas |
| Red | — | PyPI y npm accesibles; googleapis.com y api.anthropic.com accesibles (401/403 sin clave); huggingface y CDN de pesos de Whisper bloqueados |

## 2. Dependencias

Backend: fastapi, uvicorn, pydantic(-settings), sqlalchemy, alembic, httpx, python-multipart,
anthropic; opcional openai-whisper (+ torch CPU). Dev: pytest, ruff.
Frontend: next 15, react 19, typescript, tailwind 4, eslint.
Sistema: ffmpeg, espeak-ng, fuentes (Inter/DejaVu ya presentes).

## 3. Costos estimados

| Ítem | Costo | Nota |
|---|---|---|
| YouTube Data API v3 | Gratis | Cuota 10.000 unidades/día. `search.list` = 100 u, `videos.list` = 1 u → ~80 búsquedas/día con el límite por defecto |
| Claude Opus 5.5 | USD 4 / 20 por MTok (entrada/salida) | Análisis ≈ 8k in + 4k out ≈ **USD 0,11**; 3 guiones ≈ 6k in + 8k out ≈ **USD 0,18**. ≈ **USD 0,30 por referencia** procesada (el razonamiento interno se factura como salida) |
| Whisper local | Gratis (CPU) | Modelo `base`: ~0,3–1× tiempo real en 4 vCPU |
| espeak-ng | Gratis | Calidad robótica; interfaz preparada para proveedores de voz premium **desactivados por defecto** |
| FFmpeg | Gratis | ~1–3 min de render por clip de 60 s en 4 vCPU |
| Remotion | Gratis para individuos y empresas ≤3 personas; **licencia paga** para organizaciones mayores | Por eso es opcional |

Controles: `LIMIT_*` en `.env`, registro `UsageEvent` con costo por operación y bloqueo al
superar presupuesto mensual o cuotas diarias.

## 4. Riesgos técnicos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Pesos de Whisper no descargables en este entorno | Bloquea transcripción automática aquí | Habilitar el host de descarga en la red del entorno, o cargar pesos manualmente (`WHISPER_MODEL` admite ruta). Alternativas siempre disponibles: subir `.srt/.vtt` o pegar transcripción |
| No se pueden descargar videos de YouTube (por diseño) | Análisis audiovisual limitado a metadatos + transcripción | Análisis completo sólo con archivos adjuntos autorizados; el informe declara qué fuentes usó |
| Sin claves reales en el entorno de desarrollo | No se puede validar YouTube/Claude end-to-end aquí | Clientes con fakes inyectables para tests; prueba real documentada con checklist al cargar claves |
| Calidad de voz de espeak-ng | Clips menos atractivos | Interfaz `TTSProvider`; admitir voz grabada por el usuario como asset |
| Material visual de apoyo | Sin stock automático (derechos) | Biblioteca de assets del usuario + fondos generados (gradientes, tipografía animada) |
| Remotion requiere navegador headless y licencia | Complejidad / costo | FFmpeg como motor principal; Remotion como complemento opcional |
| Crecimiento con una sola medición | Conclusiones engañosas | Snapshots históricos; la UI muestra "sin datos suficientes" con <2 mediciones |
| Copia involuntaria de la referencia | Riesgo legal/ético | Prompt explícito + chequeo de n-gramas compartidos contra la transcripción; se rechaza/regenera si supera umbral |
| Tareas largas en requests HTTP | Timeouts | Jobs persistidos + polling |

## 5. Fases

| Fase | Entregable verificable |
|---|---|
| 1 Arquitectura y configuración | Backend/Frontend arrancan; `/api/system/status` real; proxy sin secretos; tests y build verdes |
| 2 Base de datos y backend | Modelos + Alembic; CRUD referencias; jobs; contador de uso/costos; dashboard con conteos reales |
| 3 YouTube | Búsqueda con filtros (keyword, categoría, idioma, país, antigüedad, duración, orden); alta por URL; snapshots y crecimiento |
| 4 Biblioteca | Búsqueda interna, filtros, etiquetas, favoritos, ficha individual, adjuntos autorizados con declaración de derechos |
| 5 Análisis | Transcripción (Whisper / SRT / manual) + informe Claude estructurado con puntaje editorial |
| 6 Guiones | 3 guiones originales por referencia, edición y aprobación, control de similitud |
| 7 Motor audiovisual | TTS + 6 plantillas + render MP4 1080x1920 H.264/AAC en 15/30/45/60 s, variantes |
| 8 Aprobación | Estados, revisión con reproductor, aprobar/rechazar, exportaciones y descarga |
| 9 Integración | Flujo completo de punta a punta en UI; manejo de errores y límites |
| 10 Pruebas y documentación | Suite ampliada, prueba e2e con Playwright, guía de uso y despliegue |
