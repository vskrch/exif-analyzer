"""
EXIF Analyzer - Application Entry Point

Run with:
    python main.py                  # Development
    uvicorn main:app --host 0.0.0.0 --port 8000  # Alternative
    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker  # Production
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import router
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.security import RequestIdMiddleware, setup_cors
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)

# Application start time for uptime metrics
_start_time = time.time()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    logger.info("%s started successfully", settings.app_name)
    yield
    logger.info("%s shutting down", settings.app_name)


def create_app() -> FastAPI:
    """
    Application factory. Creates and configures the FastAPI app.
    """
    settings = get_settings()

    # Set up logging before anything else
    setup_logging()

    logger.info("Initializing %s v%s [%s]", settings.app_name, __version__, settings.app_env)

    # Create FastAPI app with lifespan
    app = FastAPI(
        title=settings.app_name,
        description="Production-grade service for analyzing image EXIF metadata",
        version=__version__,
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        openapi_url="/openapi.json" if settings.app_debug else None,
        lifespan=lifespan,
    )

    # --- Middleware (order matters: last added = first executed) ---

    # Request ID (outermost)
    app.add_middleware(RequestIdMiddleware)

    # CORS
    setup_cors(app)

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Static files ---
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # --- Routes ---
    app.include_router(router)

    logger.info("Application configured: %s", settings.app_name)
    return app


# Create the ASGI application instance
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
