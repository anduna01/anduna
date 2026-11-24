# Viral Clip Factory

Fábrica semiautomática de clips verticales a partir de referencias exitosas de YouTube:
investigación → análisis con Claude → guiones originales → producción con FFmpeg →
aprobación humana → exportación MP4.

## Requisitos
Python ≥3.11 con [uv](https://docs.astral.sh/uv/), Node ≥20, FFmpeg con libx264/aac/libass.

## Puesta en marcha
```bash
cp .env.example .env        # completar ANTHROPIC_API_KEY y YOUTUBE_API_KEY
make setup
make backend                # http://127.0.0.1:8000/docs
make frontend               # http://localhost:3000
make test
```

Documentación: [`CLAUDE.md`](CLAUDE.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
[`docs/PLAN.md`](docs/PLAN.md) · [`docs/CHANGELOG.md`](docs/CHANGELOG.md)

> `index.html` en la raíz es un proyecto previo independiente (calculadora).
