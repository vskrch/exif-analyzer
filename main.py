"""
EXIF Analyzer - Application Entry Point

Run with:
    python main.py                  # Development
    uvicorn main:app --host 0.0.0.0 --port 8000  # Alternative
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi.middleware import SlowAPIMiddleware

from app import __version__
from app.api import router
from app.api.dependencies import limiter
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.security import (
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    setup_cors,
    setup_trusted_hosts,
)
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    # Ensure log directory exists
    Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)
    logger.info("%s v%s started [%s]", settings.app_name, __version__, settings.app_env)
    yield
    logger.info("%s shutting down", settings.app_name)


def create_app() -> FastAPI:
    """Application factory. Creates and configures the FastAPI app."""
    settings = get_settings()
    setup_logging()

    logger.info("Initializing %s v%s [%s]", settings.app_name, __version__, settings.app_env)

    app = FastAPI(
        title=settings.app_name,
        description="Production-grade service for analyzing image EXIF metadata",
        version=__version__,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        openapi_url="/openapi.json" if settings.app_debug else None,
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # Security middleware (last added = first executed)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    setup_trusted_hosts(app)
    setup_cors(app)

    register_exception_handlers(app)

    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(router)

    logger.info("Application configured: %s", settings.app_name)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    logger.info(
        "Starting server at http://%s:%d (debug=%s)",
        settings.host,
        settings.port,
        settings.app_debug,
    )
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_debug,
        workers=settings.workers if not settings.app_debug else 1,
        log_level=settings.log_level.lower(),
    )
