"""Integration tests that require a live PostgreSQL instance.

These tests are skipped when ``DATABASE_URL`` is not present in the
environment. They never create, migrate or drop schemas.
"""

from __future__ import annotations

import os

import pytest

from app.api.v1.health import DependencyStatus, check_database
from app.core.config import Settings

DATABASE_URL = os.getenv("DATABASE_URL")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL is not configured"),
]


async def test_probe_reports_ok_for_a_reachable_database() -> None:
    settings = Settings(database_url=DATABASE_URL)

    result = await check_database(settings)

    assert result.status is DependencyStatus.OK
    assert result.detail is None


async def test_probe_reports_unavailable_for_an_unreachable_database() -> None:
    settings = Settings(database_url="postgresql://nobody:nobody@127.0.0.1:1/none")

    result = await check_database(settings)

    assert result.status is DependencyStatus.UNAVAILABLE
    assert result.detail is not None
