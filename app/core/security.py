"""
Security middleware and upload validation.
"""

import logging
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from app.config import get_settings
from app.core.exceptions import (
    EmptyFileError,
    FileTooLargeError,
    InvalidFileTypeError,
    InvalidImageContentError,
)
from app.logging_config import request_id_filter

logger = logging.getLogger(__name__)

CHUNK_SIZE = 8192

# Extension -> acceptable file signatures (prefix bytes)
IMAGE_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".gif": (b"GIF87a", b"GIF89a"),
    ".tiff": (b"II*\x00", b"MM\x00*"),
    ".tif": (b"II*\x00", b"MM\x00*"),
    ".bmp": (b"BM",),
    ".webp": (b"RIFF",),  # RIFF....WEBP verified below
}


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attaches a unique request ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_filter.set_request_id(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' blob:"
        )
        return response


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware from application settings."""
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )


def setup_trusted_hosts(app: FastAPI) -> None:
    """Restrict Host header in production."""
    settings = get_settings()
    if settings.is_production and settings.trusted_host_list:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)


def sanitize_filename(filename: str | None) -> str:
    """Return a safe basename for display (no path traversal)."""
    if not filename:
        return "upload"
    clean = os.path.basename(filename.replace("\x00", "")).strip()
    return clean[:255] if clean else "upload"


def _matches_signature(contents: bytes, ext: str) -> bool:
    """Verify file magic bytes match the declared extension."""
    signatures = IMAGE_SIGNATURES.get(ext)
    if not signatures:
        return False

    if ext == ".webp":
        return contents.startswith(b"RIFF") and len(contents) >= 12 and contents[8:12] == b"WEBP"

    return any(contents.startswith(sig) for sig in signatures)


async def validate_upload(file: UploadFile) -> bytes:
    """
    Validate and read an uploaded file with chunked size checks and magic-byte verification.

    Raises:
        InvalidFileTypeError: Extension not allowed or content mismatch.
        FileTooLargeError: File exceeds configured size.
        EmptyFileError: Zero-byte upload.
        InvalidImageContentError: Content does not match a known image format.
    """
    settings = get_settings()

    filename = sanitize_filename(file.filename)
    ext = Path(filename).suffix.lower()
    if ext not in settings.allowed_extension_set:
        raise InvalidFileTypeError(allowed=", ".join(sorted(settings.allowed_extension_set)))

    chunks: list[bytes] = []
    total_size = 0

    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > settings.max_upload_size_bytes:
            raise FileTooLargeError(max_size_mb=settings.max_upload_size_mb)
        chunks.append(chunk)

    contents = b"".join(chunks)

    if total_size == 0:
        raise EmptyFileError()

    if not _matches_signature(contents, ext):
        raise InvalidImageContentError()

    await file.seek(0)
    return contents
