# EXIF Analyzer

Production-grade web application for analyzing image EXIF metadata. Upload an image and get categorized metadata — camera settings, GPS, timestamps, and more.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-33%20passed-2ecc71?logo=pytest&logoColor=white)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-86%25-3498db)](tests/)
[![License: MIT](https://img.shields.io/badge/license-MIT-667eea)](LICENSE)

## Features

- **EXIF extraction** — Parses 50+ tags and groups them into Camera, Date/Time, GPS, Settings, and more
- **Web UI** — Drag-and-drop upload with a responsive, collapsible results view
- **REST API** — `POST /analyze` returns structured JSON; consistent error responses
- **Production foundations** — Structured logging, request tracing, file validation, CORS, health checks
- **Containerized** — Multi-stage Docker build with non-root user and health checks
- **CI/CD** — GitHub Actions runs lint, tests, and Docker build on every push

## Quick Start

### Local

```bash
git clone https://github.com/vskrch/exif-analyzer.git
cd exif-analyzer

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env

python main.py
```

Open [http://localhost:8000](http://localhost:8000).

### Docker

```bash
# Production
docker compose up -d

# Development (hot reload)
docker compose --profile dev up dev
```

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Web UI |
| `POST` | `/analyze` | Upload an image, receive categorized EXIF data |
| `GET` | `/health` | Service health, version, environment |
| `GET` | `/docs` | OpenAPI docs (debug mode only) |

**Success response** (`POST /analyze`):

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
    "Camera Settings": [
      { "tag": "FNumber", "value": "2.8" },
      { "tag": "ISOSpeedRatings", "value": "400" }
    ]
  }
}
```

**Error response**:

```json
{
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File too large. Maximum size is 25MB."
  }
}
```

| Code | HTTP | Meaning |
|------|------|---------|
| `INVALID_FILE_TYPE` | 415 | Extension not allowed |
| `FILE_TOO_LARGE` | 413 | Exceeds `MAX_UPLOAD_SIZE_MB` |
| `NO_EXIF_DATA` | 422 | Image has no EXIF metadata |
| `EXIF_PROCESSING_ERROR` | 422 | Image could not be parsed |

## Project Structure

```
exif-analyzer/
├── main.py                 # App factory and entry point
├── app/
│   ├── config.py           # Settings (pydantic-settings)
│   ├── logging_config.py   # Structured logging
│   ├── core/
│   │   ├── exceptions.py   # Custom errors and handlers
│   │   └── security.py     # CORS, request ID, upload validation
│   ├── api/
│   │   └── routes.py       # Route handlers
│   ├── services/
│   │   └── exif_service.py # EXIF extraction and categorization
│   └── schemas/
│       └── exif.py         # Pydantic response models
├── templates/index.html
├── static/css/style.css
├── static/js/app.js
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Development

```bash
pip install -r requirements-dev.txt

# Tests
pytest
pytest --cov=app --cov-report=term-missing

# Lint and format
ruff check .
ruff format .
```

## Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | `development`, `production`, or `testing` |
| `APP_DEBUG` | `false` | Enables `/docs` and hot reload |
| `PORT` | `8000` | Server port |
| `MAX_UPLOAD_SIZE_MB` | `25` | Max upload size |
| `ALLOWED_EXTENSIONS` | `.jpg,.jpeg,.png,...` | Permitted file types |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `CORS_ORIGINS` | `http://localhost:8000` | Allowed origins |

## Supported Formats

| Format | EXIF support |
|--------|--------------|
| JPEG / JPG | Full |
| TIFF | Full |
| PNG, WebP, HEIC | Limited |
| BMP, GIF | None |

## Deployment

**Docker Compose** (recommended):

```bash
docker compose up -d
```

**Gunicorn**:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

Set these in production:

```bash
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=<random-secret>
CORS_ORIGINS=https://yourdomain.com
```

## License

MIT
