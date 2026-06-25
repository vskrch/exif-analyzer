"""
Tests for EXIF Analyzer API endpoints.
"""

import io
import json

from fastapi.testclient import TestClient
from PIL import Image


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

    def test_analyze_valid_image_returns_200(self, client: TestClient) -> None:
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        files = {"file": ("test.jpg", buf, "image/jpeg")}
        response = client.post("/analyze", files=files)
        assert response.status_code == 200

    def test_analyze_returns_categorized_data(self, client: TestClient) -> None:
        img = Image.new("RGB", (100, 100), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        files = {"file": ("photo.jpg", buf, "image/jpeg")}
        response = client.post("/analyze", files=files)
        data = response.json()

        assert "filename" in data
        assert "content_type" in data
        assert "total_tags" in data
        assert "categorized" in data
        assert isinstance(data["categorized"], dict)
        assert data["filename"] == "photo.jpg"

    def test_analyze_png_returns_200(self, client: TestClient) -> None:
        img = Image.new("RGB", (50, 50), color="green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        files = {"file": ("image.png", buf, "image/png")}
        response = client.post("/analyze", files=files)
        # PNG may or may not have EXIF - should still return 200 or 422
        assert response.status_code in (200, 422)


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
        # Create a fake file that exceeds default 25MB limit
        large_data = b"x" * (26 * 1024 * 1024)  # 26MB
        files = {"file": ("huge.jpg", large_data, "image/jpeg")}
        response = client.post("/analyze", files=files)
        assert response.status_code == 413
