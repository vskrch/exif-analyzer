# EXIF Analyzer

Production-grade web application for analyzing EXIF metadata from images. Built with FastAPI, Pydantic, and a modern responsive UI.

## Features

- Drag & drop or click to upload images
- Categorized EXIF data display (Camera, Date, GPS, Settings, etc.)
- Structured logging with request tracing
- Global error handling with consistent JSON responses
- File upload validation (type, size, extension)
- Rate limiting support (via SlowAPI)
- Health check endpoint for monitoring
- API versioning ready
- Docker support with multi-stage builds
- CI/CD pipeline with GitHub Actions

## Quick Start

### Local Development

```bash
# Clone the repository
git clone <repo-url> && cd exif-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env

# Run the application
python main.py
```

Open your browser to: **http://localhost:8000**

### Docker

```bash
# Production mode
docker compose up -d

# Development mode (with hot reload)
docker compose --profile dev up dev
```

### Docker (standalone)

```bash
# Build
docker build -t exif-analyzer .

# Run
docker run -p 8000:8000 exif-analyzer
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Web GUI |
| `POST` | `/analyze` | Upload and analyze image EXIF data |
| `GET` | `/health` | Health check (service status, version, environment) |
| `GET` | `/docs` | Interactive API docs (debug mode only) |

## Project Structure

```
exif-analyzer/
├── main.py                      # Application factory & entry point
├── app/
│   ├── __init__.py              # Version info
│   ├── config.py                # Pydantic-settings configuration
│   ├── logging_config.py        # Structured logging setup
│   ├── core/
│   │   ├── exceptions.py        # Custom exceptions & handlers
│   │   └── security.py          # CORS, rate limiting, file validation
│   ├── api/
│   │   ├── routes.py            # Route handlers
│   │   └── dependencies.py      # Shared dependencies
│   ├── services/
│   │   └── exif_service.py      # EXIF extraction & categorization
│   └── schemas/
│       └── exif.py              # Pydantic response models
├── templates/
│   └── index.html               # Jinja2 HTML template
├── static/
│   ├── css/style.css            # Stylesheet
│   └── js/app.js                # Client-side JavaScript
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_exif_api.py         # API endpoint tests
│   └── test_exif_service.py     # Service unit tests
├── Dockerfile                   # Multi-stage production Docker image
├── docker-compose.yml           # Docker Compose (prod + dev profiles)
├── pyproject.toml               # Tool configuration (pytest, ruff, mypy)
├── requirements.txt             # Production dependencies
└── requirements-dev.txt         # Dev/test dependencies
```

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_exif_api.py -v
```

## Linting & Formatting

```bash
# Check code
ruff check .

# Auto-fix
ruff check --fix .

# Format
ruff format .
```

## Configuration

All configuration is managed via environment variables (or `.env` file). See `.env.example` for all available settings.

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment: `development`, `production`, `testing` |
| `APP_DEBUG` | `false` | Enable debug mode (API docs, hot reload) |
| `PORT` | `8000` | Server port |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum upload file size in MB |
| `ALLOWED_EXTENSIONS` | `.jpg,.jpeg,.png,...` | Comma-separated allowed file extensions |
| `RATE_LIMIT_PER_MINUTE` | `30` | Requests per minute limit |
| `LOG_LEVEL` | `INFO` | Logging level: DEBUG, INFO, WARNING, ERROR |

## Supported Image Formats

- JPEG / JPG
- PNG (limited EXIF support)
- TIFF
- WebP
- HEIC / HEIF (with Pillow 10.1+)
- BMP
- GIF

## License

MIT
