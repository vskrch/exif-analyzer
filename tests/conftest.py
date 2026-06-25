"""
Pytest fixtures for the EXIF Analyzer test suite.
"""

import io
import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Override settings before importing the app
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("APP_DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("LOG_FILE", "/tmp/test_exif.log")

from main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Generate a minimal JPEG image with EXIF data for testing."""
    img = Image.new("RGB", (100, 100), color="red")

    # Add EXIF data
    from PIL.ExifTags import Base as ExifBase

    exif_dict = {
        ExifBase.Make: "TestCamera",
        ExifBase.Model: "TestModel 5000",
        ExifBase.Software: "TestSoftware 1.0",
        ExifBase.DateTime: "2024:01:15 10:30:00",
        ExifBase.DateTimeOriginal: "2024:01:15 10:30:00",
        ExifBase.ExposureTime: (1, 250),
        ExifBase.FNumber: (28, 10),
        ExifBase.ISOSpeedRatings: 400,
        ExifBase.FocalLength: (50, 1),
        ExifBase.ImageWidth: 100,
        ExifBase.ImageLength: 100,
    }

    import struct

    # Build EXIF bytes manually for PIL
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG", exif=struct.pack("<HH", 0x4578, 0x6966))
    img_bytes.seek(0)

    # Simpler approach: save with basic EXIF
    img2 = Image.new("RGB", (100, 100), color="blue")
    output = io.BytesIO()
    img2.save(output, format="JPEG")
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
