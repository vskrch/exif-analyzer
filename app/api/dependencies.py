"""
Shared FastAPI dependencies (rate limiter, etc.).
"""

import logging

from fastapi import Request, UploadFile

from app.config import get_settings
from app.core.exceptions import FileTooLargeError, InvalidFileTypeError

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str | None:
    """Extract request ID from request headers."""
    return request.headers.get("X-Request-ID")


async def validate_upload(file: UploadFile) -> bytes:
    """
    Validate an uploaded file against configured limits.
    Returns file contents if valid, raises exceptions otherwise.
    """
    from pathlib import Path

    settings = get_settings()

    # Validate extension
    filename = file.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extension_set:
        raise InvalidFileTypeError(allowed=", ".join(sorted(settings.allowed_extension_set)))

    # Read contents with size check
    chunks: list[bytes] = []
    total_size = 0
    while True:
        chunk = await file.read(8192)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > settings.max_upload_size_bytes:
            raise FileTooLargeError(max_size_mb=settings.max_upload_size_mb)
        chunks.append(chunk)

    contents = b"".join(chunks)
    await file.seek(0)
    return contents
