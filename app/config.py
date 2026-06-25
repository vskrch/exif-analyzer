"""
Application configuration using pydantic-settings.
All settings are loaded from environment variables or .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "EXIF Analyzer"
    app_env: str = "development"
    app_debug: bool = False
    app_url: str = "http://localhost:8000"
    secret_key: str = "change-me-in-production"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Upload
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 25
    allowed_extensions: str = ".jpg,.jpeg,.png,.tiff,.tif,.webp,.heic,.heif,.bmp,.gif"

    # Rate Limiting
    rate_limit_per_minute: int = 30
    rate_limit_upload_per_minute: int = 10

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_extension_set(self) -> set:
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",")}

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @field_validator("upload_dir")
    @classmethod
    def ensure_upload_dir(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
