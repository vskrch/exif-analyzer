"""
Tests for EXIF Analyzer API endpoints.
"""

import io

from fastapi.testclient import TestClient
from PIL import Image


def _make_jpeg_with_exif() -> io.BytesIO:
    """Create a minimal JPEG with EXIF data for testing."""
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()

    # PIL can embed EXIF data via the 'exif' parameter in save()
    # Build a minimal EXIF byte segment
    import struct

    # TIFF header with IFD entries
    # This creates a minimal valid EXIF block
    exif_header = b"Exif\x00\x00"
    # TIFF header (little-endian)
    tiff_header = b"II"  # Intel byte order
    tiff_header += struct.pack("<H", 42)  # Magic number
    tiff_header += struct.pack("<I", 8)  # Offset to first IFD

    # IFD entries (count + entries)
    # We'll include Make (0x010F), Model (0x0110), DateTime (0x0132)
    num_entries = struct.pack("<H", 3)

    # Make entry: "TestCamera"
    make_val = b"TestCamera\x00"
    make_offset = 8 + 2 + 3 * 12 + 4  # after IFD entries + next IFD pointer
    entry_make = struct.pack("<HHII", 0x010F, 2, 11, make_offset)

    # Model entry: "TestModel"
    model_val = b"TestModel\x00"
    model_offset = make_offset + len(make_val)
    entry_model = struct.pack("<HHII", 0x0110, 2, 10, model_offset)

    # DateTime entry: "2024:01:15 10:30:00"
    dt_val = b"2024:01:15 10:30:00\x00"
    dt_offset = model_offset + len(model_val)
    entry_dt = struct.pack("<HHII", 0x0132, 2, 20, dt_offset)

    next_ifd = struct.pack("<I", 0)  # No more IFDs

    tiff_data = tiff_header + num_entries + entry_make + entry_model + entry_dt + next_ifd
    tiff_data += make_val + model_val + dt_val

    full_exif = exif_header + tiff_data

    img.save(buf, format="JPEG", exif=full_exif)
    buf.seek(0)
    return buf


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_expected_fields(self, client: TestClient) -> None:
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] == "healthy"

    def test_health_content_type(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"


class TestAnalyzeEndpoint:
    """Tests for the /analyze endpoint."""

    def test_analyze_no_file_returns_422(self, client: TestClient) -> None:
        response = client.post("/analyze")
        assert response.status_code == 422

    def test_analyze_invalid_file_type_returns_415(self, client: TestClient) -> None:
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        response = client.post("/analyze", files=files)
        assert response.status_code == 415
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_FILE_TYPE"

    def test_analyze_image_with_exif_returns_200(self, client: TestClient) -> None:
        buf = _make_jpeg_with_exif()
        files = {"file": ("test.jpg", buf, "image/jpeg")}
        response = client.post("/analyze", files=files)
        assert response.status_code == 200

    def test_analyze_returns_categorized_data(self, client: TestClient) -> None:
        buf = _make_jpeg_with_exif()
        files = {"file": ("photo.jpg", buf, "image/jpeg")}
        response = client.post("/analyze", files=files)
        data = response.json()

        assert "filename" in data
        assert "content_type" in data
        assert "total_tags" in data
        assert "categorized" in data
        assert isinstance(data["categorized"], dict)
        assert data["filename"] == "photo.jpg"
        assert data["total_tags"] > 0

    def test_analyze_image_without_exif_returns_422(self, client: TestClient) -> None:
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        files = {"file": ("test.jpg", buf, "image/jpeg")}
        response = client.post("/analyze", files=files)
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "NO_EXIF_DATA"

    def test_analyze_png_without_exif_returns_422(self, client: TestClient) -> None:
        img = Image.new("RGB", (50, 50), color="green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        files = {"file": ("image.png", buf, "image/png")}
        response = client.post("/analyze", files=files)
        assert response.status_code == 422


class TestRootEndpoint:
    """Tests for the / endpoint (web GUI)."""

    def test_root_returns_html(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_root_contains_exif_analyzer_title(self, client: TestClient) -> None:
        response = client.get("/")
        assert "EXIF Analyzer" in response.text

    def test_root_references_static_assets(self, client: TestClient) -> None:
        response = client.get("/")
        assert "/static/css/style.css" in response.text
        assert "/static/js/app.js" in response.text


class TestStaticAssets:
    """Tests for static file serving."""

    def test_css_returns_200(self, client: TestClient) -> None:
        response = client.get("/static/css/style.css")
        assert response.status_code == 200

    def test_js_returns_200(self, client: TestClient) -> None:
        response = client.get("/static/js/app.js")
        assert response.status_code == 200


class TestErrorHandling:
    """Tests for error response format consistency."""

    def test_invalid_file_type_error_format(self, client: TestClient) -> None:
        files = {"file": ("test.pdf", b"%PDF-1.4", "application/pdf")}
        response = client.post("/analyze", files=files)
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

    def test_large_file_returns_413(self, client: TestClient) -> None:
        large_data = b"x" * (26 * 1024 * 1024)  # 26MB
        files = {"file": ("huge.jpg", large_data, "image/jpeg")}
        response = client.post("/analyze", files=files)
        assert response.status_code == 413

    def test_no_exif_error_format(self, client: TestClient) -> None:
        img = Image.new("RGB", (10, 10), color="white")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        files = {"file": ("noexif.jpg", buf, "image/jpeg")}
        response = client.post("/analyze", files=files)
        data = response.json()
        assert data["error"]["code"] == "NO_EXIF_DATA"
        assert "No EXIF data" in data["error"]["message"]
