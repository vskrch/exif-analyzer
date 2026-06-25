"""
Security middleware: CORS, rate limiting, file validation, request ID.
"""

import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import get_settings
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError
from app.logging_config import request_id_filter

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attaches a unique request ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_filter.set_request_id(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware from application settings."""
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_request_id(app: FastAPI) -> None:
    """Add request ID middleware."""
    app.add_middleware(RequestIdMiddleware)


async def validate_upload_file(
    file: UploadFile, max_size_mb: int, allowed_extensions: set
) -> bytes:
    """
    Validate and read an uploaded file.
    Checks file extension and size before returning contents.

    Raises:
        InvalidFileTypeError: If file extension is not allowed.
        FileTooLargeError: If file exceeds maximum size.
    """
    # Validate extension
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise InvalidFileTypeError(allowed=", ".join(sorted(allowed_extensions)))

    # Read contents
    contents = await file.read()

    # Validate size
    if len(contents) > max_size_mb * 1024 * 1024:
        raise FileTooLargeError(max_size_mb=max_size_mb)

    # Reset file position for downstream processing
    await file.seek(0)

    return contents
