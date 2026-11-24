import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import dashboard, jobs, references, system
from app.core.config import get_settings
from app.core.errors import InvalidTransition, NotFound, ProviderDisabled, UsageLimitExceeded
from app.db.migrate import upgrade_to_head
from app.services import jobs as job_service
from app.services import selftest  # noqa: F401  (registra el handler)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    upgrade_to_head()
    if settings.jobs_worker_enabled:
        job_service.start_worker()
    yield
    job_service.stop_worker()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(NotFound)
    async def _nf(_: Request, exc: NotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(UsageLimitExceeded)
    async def _limit(_: Request, exc: UsageLimitExceeded):
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    @app.exception_handler(ProviderDisabled)
    async def _disabled(_: Request, exc: ProviderDisabled):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(InvalidTransition)
    async def _transition(_: Request, exc: InvalidTransition):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    for r in (system, dashboard, references, jobs):
        app.include_router(r.router, prefix="/api")
    return app


app = create_app()
