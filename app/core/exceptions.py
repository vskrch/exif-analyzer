"""
Custom exception classes and global exception handlers.
"""

import logging
from typing import Any, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception with HTTP status code and error code."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred",
        error_code: str = "INTERNAL_ERROR",
        headers: Optional[dict] = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.headers = headers
        super().__init__(detail)


class FileTooLargeError(AppException):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, max_size_mb: int) -> None:
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size_mb}MB.",
            error_code="FILE_TOO_LARGE",
        )


class InvalidFileTypeError(AppException):
    """Raised when uploaded file has disallowed extension."""

    def __init__(self, allowed: str) -> None:
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Invalid file type. Allowed: {allowed}",
            error_code="INVALID_FILE_TYPE",
        )


class NoExifDataError(AppException):
    """Raised when an image contains no EXIF data."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No EXIF data found in this image.",
            error_code="NO_EXIF_DATA",
        )


class ExifProcessingError(AppException):
    """Raised when EXIF extraction fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to process image EXIF data: {reason}",
            error_code="EXIF_PROCESSING_ERROR",
        )


class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            error_code="RATE_LIMIT_EXCEEDED",
            headers={"Retry-After": "60"},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                }
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            },
        )
