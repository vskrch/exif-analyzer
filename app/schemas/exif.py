"""
Pydantic models for EXIF analysis responses.
"""

from pydantic import BaseModel, Field


class ExifTag(BaseModel):
    """A single EXIF tag with its value."""

    tag: str = Field(..., description="EXIF tag name")
    value: str = Field(..., description="Formatted EXIF value")


class ExifAnalysisResponse(BaseModel):
    """Response model for EXIF analysis endpoint."""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the uploaded file")
    total_tags: int = Field(..., description="Total number of EXIF tags found")
    categorized: dict[str, list[ExifTag]] = Field(..., description="EXIF data grouped by category")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: dict[str, str] = Field(
        ...,
        description="Error details with code and message",
        examples=[{"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong"}}],
    )
