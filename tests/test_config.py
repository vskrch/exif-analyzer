"""Tests for production configuration validation."""

import pytest

from app.config import INSECURE_DEFAULT_SECRET, Settings, get_settings


class TestProductionConfig:
    """Settings must reject unsafe production configuration."""

    def test_production_rejects_default_secret(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("SECRET_KEY", INSECURE_DEFAULT_SECRET)
        monkeypatch.setenv("APP_DEBUG", "false")
        with pytest.raises(ValueError, match="SECRET_KEY"):
            Settings()

    def test_production_rejects_debug_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("SECRET_KEY", "a-secure-production-secret-key-here")
        monkeypatch.setenv("APP_DEBUG", "true")
        with pytest.raises(ValueError, match="APP_DEBUG"):
            Settings()

    def test_testing_env_allows_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "testing")
        settings = Settings()
        assert settings.app_env == "testing"

    def teardown_method(self) -> None:
        get_settings.cache_clear()
