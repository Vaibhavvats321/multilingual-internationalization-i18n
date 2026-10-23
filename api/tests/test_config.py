"""Tests for the settings contract."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import PLACEHOLDER_SESSION_SECRET, Settings


def test_cors_origins_are_split_on_commas() -> None:
    settings = Settings(cors_origins="http://localhost:3000, https://app.example.com")

    assert settings.cors_origins == ["http://localhost:3000", "https://app.example.com"]


def test_wildcard_cors_origin_is_rejected() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(cors_origins="*")


def test_production_rejects_the_placeholder_session_secret() -> None:
    with pytest.raises(ValidationError, match="SESSION_SECRET"):
        Settings(
            app_env="production",
            database_url="postgresql://user:pass@localhost:5432/db",
            session_secret=PLACEHOLDER_SESSION_SECRET,
        )


def test_production_requires_a_database_url() -> None:
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(_env_file=None, app_env="production", session_secret="a-real-secret")


def test_translation_provider_requires_an_api_key() -> None:
    with pytest.raises(ValidationError, match="TRANSLATION_API_KEY"):
        Settings(translation_provider="openai", translation_api_key=None)


def test_secrets_are_not_exposed_by_repr() -> None:
    settings = Settings(session_secret="super-secret-value")

    assert "super-secret-value" not in repr(settings)
    assert settings.session_secret.get_secret_value() == "super-secret-value"


def test_base_urls_must_be_absolute() -> None:
    with pytest.raises(ValidationError, match="absolute http"):
        Settings(api_base_url="localhost:8000")
