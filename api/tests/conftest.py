"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Settings with no external dependency configured."""
    return Settings(
        _env_file=None,
        app_env="local",
        database_url=None,
        cors_origins=["http://localhost:3000"],
        log_level="warning",
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    """Application instance built from the test settings."""
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """HTTP client bound to the application under test."""
    with TestClient(app) as test_client:
        yield test_client
