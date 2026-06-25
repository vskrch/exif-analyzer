<p align="center">
  <img src="https://img.shields.io/badge/Version-2.0.0-764ba2?style=for-the-badge&logo=python&logoColor=white" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-667eea?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Tests-33%20Passed-2ecc71?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests">
  <img src="https://img.shields.io/badge/Coverage-86%25-3498db?style=for-the-badge" alt="Coverage">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" alt="CI">
</p>

<h1 align="center">
  <br>
  :camera: EXIF Analyzer
  <br>
</h1>

<h4 align="center">Production-grade SaaS application for analyzing image EXIF metadata</h4>

<p align="center">
  Built with <a href="https://fastapi.tiangolo.com" target="_blank"><b>FastAPI</b></a> &bull;
  <a href="https://docs.pydantic.dev" target="_blank"><b>Pydantic</b></a> &bull;
  <a href="https://pillow.readthedocs.io" target="_blank"><b>Pillow</b></a> &bull;
  <a href="https://www.docker.com" target="_blank"><b>Docker</b></a>
</p>

<p align="center">
  <a href="#-features">Features</a> &bull;
  <a href="#-quick-start">Quick Start</a> &bull;
  <a href="#-api-reference">API</a> &bull;
  <a href="#-testing">Tests</a> &bull;
  <a href="#-configuration">Config</a> &bull;
  <a href="#-deployment">Deploy</a>
</p>

---

## :sparkles: Features

| Feature | Description |
|:--------|:------------|
| :gear: **Smart EXIF Parsing** | Extracts and categorizes 50+ EXIF tags into logical groups |
| :art: **Beautiful UI** | Modern responsive interface with drag-and-drop upload |
| :shield: **Security First** | CORS, file validation, rate limiting, request tracing |
| :mag: **Structured Logging** | Rotating logs with request IDs for debugging |
| :hospital: **Health Monitoring** | `/health` endpoint with version and environment info |
| :rocket: **Production Ready** | Docker multi-stage builds, non-root containers |
| :test_tube: **86% Test Coverage** | 33 tests covering API endpoints and business logic |
| :octocat: **CI/CD Pipeline** | GitHub Actions: lint, test, Docker build on every push |

---

## :rocket: Quick Start

### Option 1: Local Development

```bash
# Clone the repository
git clone <repo-url> && cd exif-analyzer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Run the application
python main.py
```

> :earth_americas: Open **http://localhost:8000** in your browser

### Option 2: Docker

```bash
# Build and run in production mode
docker compose up -d

# Or run with hot-reload for development
docker compose --profile dev up dev
```

### Option 3: Docker Standalone

```bash
docker build -t exif-analyzer .
docker run -p 8000:8000 exif-analyzer
```

---

## :electric_plug: API Reference

| Method | Endpoint | Description | Status Codes |
|:------:|:---------|:------------|:-------------|
| `GET` | `/` | Web GUI | `200` |
| `POST` | `/analyze` | Upload and analyze image | `200`, `413`, `415`, `422` |
| `GET` | `/health` | Health check | `200` |
| `GET` | `/docs` | Interactive API docs | `200` |

### Example Response

```json
{
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "total_tags": 24,
  "categorized": {
    "Camera & Device": [
      { "tag": "Make", "value": "Canon" },
      { "tag": "Model", "value": "EOS R5" }
    ],
    "Date & Time": [
      { "tag": "DateTimeOriginal", "value": "2024:01:15 10:30:00" }
    ],
    "Camera Settings": [
      { "tag": "FNumber", "value": "2.8000" },
      { "tag": "ISOSpeedRatings", "value": "400" }
    ]
  }
}
```

### Error Response Format

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File too large. Maximum size is 25MB."
  }
}
```

---

## :card_file_box: Project Structure

```
exif-analyzer/
:point_right: main.py                      # Application factory & entry point
:point_right: app/
:point_right: :---: __init__.py              # Version info (v2.0.0)
:point_right: :---: config.py                # pydantic-settings configuration
:point_right: :---: logging_config.py        # Structured logging setup
:point_right: :---: core/
:point_right: :------: exceptions.py        # Custom exceptions & global handlers
:point_right: :------: security.py          # CORS, request ID, file validation
:point_right: :---: api/
:point_right: :------: routes.py            # Route handlers (/analyze, /health)
:point_right: :------: dependencies.py      # Shared validation utilities
:point_right: :---: services/
:point_right: :------: exif_service.py      # EXIF extraction & categorization
:point_right: :---: schemas/
:point_right: :------: exif.py              # Pydantic response models
:point_right: templates/
:point_right: :---: index.html               # Jinja2 HTML template
:point_right: static/
:point_right: :---: css/style.css            # Modern responsive stylesheet
:point_right: :---: js/app.js                # Client-side JavaScript
:point_right: tests/
:point_right: :---: conftest.py              # Pytest fixtures
:point_right: :---: test_exif_api.py         # 17 API endpoint tests
:point_right: :---: test_exif_service.py     # 16 service unit tests
:point_right: Dockerfile                   # Multi-stage production image
:point_right: docker-compose.yml           # Docker Compose (prod + dev)
:point_right: .github/workflows/ci.yml     # GitHub Actions CI pipeline
:point_right: pyproject.toml               # ruff, pytest, mypy config
```

---

## :test_tube: Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests (33 tests)
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_exif_api.py -v
```

### Test Coverage

| Module | Coverage |
|:-------|:--------:|
| `app/api/routes.py` | :green_circle: 100% |
| `app/core/security.py` | :green_circle: 97% |
| `app/logging_config.py` | :green_circle: 98% |
| `app/config.py` | :green_circle: 95% |
| `app/core/exceptions.py` | :green_circle: 91% |
| `app/services/exif_service.py` | :green_circle: 88% |
| **Overall** | :green_circle: **86%** |

---

## :art: Linting & Formatting

```bash
# Check code for issues
ruff check .

# Auto-fix safe issues
ruff check --fix .

# Format all files
ruff format .
```

---

## :wrench: Configuration

All settings are managed via environment variables (or `.env` file).

| Variable | Default | Description |
|:---------|:--------|:------------|
| `APP_ENV` | `development` | `development`, `production`, `testing` |
| `APP_DEBUG` | `false` | Enable API docs and hot reload |
| `PORT` | `8000` | Server port |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum file upload size |
| `ALLOWED_EXTENSIONS` | `.jpg,.jpeg,.png,...` | Allowed image file types |
| `RATE_LIMIT_PER_MINUTE` | `30` | API rate limit |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Allowed CORS origins |

---

## :camera: Supported Image Formats

| Format | EXIF Support | Notes |
|:-------|:------------:|:------|
| JPEG / JPG | :large_blue_circle: Full | Best EXIF support |
| TIFF | :large_blue_circle: Full | Full metadata |
| PNG | :large_orange_circle: Limited | Basic EXIF only |
| WebP | :large_orange_circle: Limited | Depends on encoder |
| HEIC / HEIF | :large_orange_circle: Limited | Requires Pillow 10.1+ |
| BMP | :red_circle: None | No EXIF data |
| GIF | :red_circle: None | No EXIF data |

---

## :package: Deployment

### Production (Docker Compose)

```bash
docker compose up -d
```

Features:
- Non-root container for security
- Health checks configured
- Volume mounts for uploads and logs
- Auto-restart on failure

### Production (Gunicorn)

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Environment Variables for Production

```bash
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=<your-secret-key>
CORS_ORIGINS=https://yourdomain.com
```

---

## :memo: License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with :heart: by <a href="https://github.com/yourusername">Your Name</a>
  <br><br>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FASTAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Ruff-0.11-D7FF64?style=for-the-badge&logo=rust&logoColor=black" alt="Ruff">
  <img src="https://img.shields.io/badge/Docker-24.0-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>
