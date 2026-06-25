"""
Application configuration using pydantic-settings.
All settings are loaded from environment variables or .env file.
"""

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEFAULT_SECRET = "change-me-in-production"


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
    secret_key: str = INSECURE_DEFAULT_SECRET

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    trusted_hosts: str = "localhost,127.0.0.1"

    # Upload
    max_upload_size_mb: int = 25
    max_image_pixels: int = 25_000_000
    allowed_extensions: str = ".jpg,.jpeg,.png,.tiff,.tif,.webp,.bmp,.gif"

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
    def allowed_extension_set(self) -> set[str]:
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",") if ext.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @field_validator("max_upload_size_mb")
    @classmethod
    def validate_max_upload_size(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("max_upload_size_mb must be between 1 and 100")
        return v

    @field_validator("rate_limit_per_minute", "rate_limit_upload_per_minute")
    @classmethod
    def validate_rate_limits(cls, v: int) -> int:
        if v < 1:
            raise ValueError("rate limits must be at least 1")
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.app_env == "production":
            if self.secret_key == INSECURE_DEFAULT_SECRET:
                raise ValueError("SECRET_KEY must be set to a secure value in production")
            if self.app_debug:
                raise ValueError("APP_DEBUG must be false in production")
            if not self.cors_origin_list:
                raise ValueError("CORS_ORIGINS must be set in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
