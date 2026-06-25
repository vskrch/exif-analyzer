"""
Pytest fixtures for the EXIF Analyzer test suite.
"""

import io
import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Override settings before importing the app
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("APP_DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("LOG_FILE", "/tmp/test_exif.log")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "1000")
os.environ.setdefault("RATE_LIMIT_UPLOAD_PER_MINUTE", "1000")

from app.config import get_settings

get_settings.cache_clear()

from main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Generate a minimal JPEG image for testing."""
    img = Image.new("RGB", (100, 100), color="red")
    output = io.BytesIO()
    img.save(output, format="JPEG")
    output.seek(0)
    return output.read()


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Generate a minimal PNG image (no EXIF) for testing."""
    img = Image.new("RGB", (50, 50), color="green")
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output.read()


@pytest.fixture
def sample_image_file(sample_jpeg_bytes: bytes) -> io.BytesIO:
    """Return sample image as a BytesIO file object."""
    return io.BytesIO(sample_jpeg_bytes)
