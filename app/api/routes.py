"""
FastAPI route definitions.
"""

import logging
import time
from typing import Dict, Any

from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__
from app.config import get_settings
from app.core.security import validate_upload_file
from app.schemas.exif import ExifAnalysisResponse, HealthResponse
from app.services.exif_service import categorize_exif, extract_exif_data

logger = logging.getLogger(__name__)

router = APIRouter()

# Application start time for uptime calculation
_start_time = time.time()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request) -> HTMLResponse:
    """Serve the main web GUI."""
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/analyze", response_model=ExifAnalysisResponse, tags=["analysis"])
async def analyze_image(file: UploadFile = File(..., description="Image file to analyze")) -> Dict[str, Any]:
    """
    Upload an image and receive its categorized EXIF metadata.

    Supports: JPG, PNG, TIFF, WebP, HEIC, BMP, GIF.
    Maximum file size: configured via MAX_UPLOAD_SIZE_MB (default 25MB).
    """
    settings = get_settings()

    logger.info("Analyzing image: %s", file.filename)

    # Validate file
    contents = await validate_upload_file(
        file, settings.max_upload_size_mb, settings.allowed_extension_set
    )

    # Extract and categorize EXIF
    exif_dict = extract_exif_data(contents)
    categorized = categorize_exif(exif_dict)

    logger.info(
        "Analysis complete for %s: %d tags across %d categories",
        file.filename,
        len(exif_dict),
        len(categorized),
    )

    return {
        "filename": file.filename,
        "content_type": file.content_type or "application/octet-stream",
        "total_tags": len(exif_dict),
        "categorized": categorized,
    }


@router.get("/health", response_model=HealthResponse, tags=["ops"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for load balancers and monitoring.
    Returns service status, version, and environment.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.app_env,
    }
