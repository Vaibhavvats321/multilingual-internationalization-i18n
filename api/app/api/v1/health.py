"""Liveness and readiness endpoints.

* ``/health/live`` answers whether the process is running. It must not touch
  any external dependency, otherwise a database outage would cause the
  orchestrator to restart an otherwise healthy process.
* ``/health/ready`` answers whether the process can serve traffic. It checks
  the configured dependencies and returns ``503`` when a required dependency
  is unavailable.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

import psycopg
from fastapi import APIRouter, Depends, Response, status
from psycopg.conninfo import conninfo_to_dict
from pydantic import BaseModel, Field

from app import __version__
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, redact

logger = get_logger("api.health")

router = APIRouter()

SERVICE_NAME = "multilingua-api"
DB_CONNECT_TIMEOUT_SECONDS = 3


class DependencyStatus(StrEnum):
    """Outcome of a single dependency check."""

    OK = "ok"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    SKIPPED = "skipped"


class DependencyCheck(BaseModel):
    """Result of checking one dependency."""

    name: str = Field(description="Dependency identifier, e.g. 'database'.")
    status: DependencyStatus
    detail: str | None = Field(default=None, description="Safe, non-sensitive context.")


class LivenessResponse(BaseModel):
    """Payload of the liveness probe."""

    status: Literal["ok"] = "ok"
    service: str = SERVICE_NAME
    version: str = __version__


class ReadinessResponse(BaseModel):
    """Payload of the readiness probe."""

    status: DependencyStatus
    service: str = SERVICE_NAME
    version: str = __version__
    checks: list[DependencyCheck] = Field(default_factory=list)


async def check_database(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DependencyCheck:
    """Verify that the configured PostgreSQL instance accepts a trivial query."""
    if settings.database_url is None:
        return DependencyCheck(
            name="database",
            status=DependencyStatus.SKIPPED,
            detail="DATABASE_URL is not configured",
        )

    dsn = settings.database_url.get_secret_value()
    password = _dsn_password(dsn)

    try:
        connection = await psycopg.AsyncConnection.connect(
            dsn,
            autocommit=True,
            connect_timeout=DB_CONNECT_TIMEOUT_SECONDS,
        )
    except psycopg.Error as exc:
        logger.warning(
            "database_connect_failed",
            error_type=type(exc).__name__,
            reason=redact(str(exc), dsn, password),
        )
        return DependencyCheck(
            name="database",
            status=DependencyStatus.UNAVAILABLE,
            detail=type(exc).__name__,
        )

    try:
        await connection.execute("SELECT 1")
    except psycopg.Error as exc:
        logger.warning(
            "database_query_failed",
            error_type=type(exc).__name__,
            reason=redact(str(exc), dsn, password),
        )
        return DependencyCheck(
            name="database",
            status=DependencyStatus.UNAVAILABLE,
            detail=type(exc).__name__,
        )
    finally:
        await connection.close()

    return DependencyCheck(name="database", status=DependencyStatus.OK)


def _dsn_password(dsn: str) -> str | None:
    """Extract the password from a connection string, if it has one."""
    try:
        password = conninfo_to_dict(dsn).get("password")
    except psycopg.Error:
        return None
    return password if isinstance(password, str) else None


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    tags=["health"],
    summary="Liveness probe",
)
async def liveness() -> LivenessResponse:
    """Report that the process is up. Never touches external dependencies."""
    return LivenessResponse()


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    tags=["health"],
    summary="Readiness probe",
)
async def readiness(
    response: Response,
    database: Annotated[DependencyCheck, Depends(check_database)],
) -> ReadinessResponse:
    """Report whether the service is able to serve traffic."""
    healthy = {DependencyStatus.OK, DependencyStatus.SKIPPED}
    overall = DependencyStatus.OK if database.status in healthy else DependencyStatus.UNAVAILABLE
    if overall is DependencyStatus.UNAVAILABLE:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status=overall, checks=[database])
