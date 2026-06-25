"""
FastAPI route definitions.
"""

import logging
from typing import Any

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app import __version__
from app.api.dependencies import limiter
from app.config import get_settings
from app.core.metrics import uptime_seconds
from app.core.security import sanitize_filename, validate_upload
from app.schemas.exif import ExifAnalysisResponse, HealthResponse
from app.services.exif_service import categorize_exif, extract_exif_data

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

_settings = get_settings()
_DEFAULT_RATE_LIMIT = f"{_settings.rate_limit_per_minute}/minute"
_UPLOAD_RATE_LIMIT = f"{_settings.rate_limit_upload_per_minute}/minute"


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
@limiter.limit(_DEFAULT_RATE_LIMIT)
async def home(request: Request) -> HTMLResponse:
    """Serve the main web GUI."""
    return templates.TemplateResponse(request, "index.html")


@router.post("/analyze", response_model=ExifAnalysisResponse, tags=["analysis"])
@limiter.limit(_UPLOAD_RATE_LIMIT)
async def analyze_image(
    request: Request,
    file: UploadFile = File(..., description="Image file to analyze"),
) -> dict[str, Any]:
    """
    Upload an image and receive its categorized EXIF metadata.

    Supports: JPG, PNG, TIFF, WebP, BMP, GIF.
    Maximum file size: configured via MAX_UPLOAD_SIZE_MB (default 25MB).
    """
    safe_name = sanitize_filename(file.filename)
    logger.info("Analyzing image: %s", safe_name)

    contents = await validate_upload(file)
    exif_dict = extract_exif_data(contents)
    categorized = categorize_exif(exif_dict)

    logger.info(
        "Analysis complete for %s: %d tags across %d categories",
        safe_name,
        len(exif_dict),
        len(categorized),
    )

    return {
        "filename": safe_name,
        "content_type": file.content_type or "application/octet-stream",
        "total_tags": len(exif_dict),
        "categorized": categorized,
    }


@router.get("/health", response_model=HealthResponse, tags=["ops"])
@limiter.limit(_DEFAULT_RATE_LIMIT)
async def health_check(request: Request) -> dict[str, str | float]:
    """
    Health check endpoint for load balancers and monitoring.
    Returns service status, version, environment, and uptime.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.app_env,
        "uptime_seconds": uptime_seconds(),
    }
