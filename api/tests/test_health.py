"""Tests for the health endpoints and the shared API conventions."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.health import DependencyCheck, DependencyStatus, check_database
from app.core.middleware import REQUEST_ID_HEADER


def test_liveness_reports_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "multilingua-api"
    assert "version" in body


def test_readiness_is_ok_when_database_is_not_configured(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    checks = body["checks"]
    assert len(checks) == 1
    assert checks[0]["name"] == "database"
    assert checks[0]["status"] in {"ok", "skipped"}
    if checks[0]["status"] == "skipped":
        assert checks[0]["detail"] == "DATABASE_URL is not configured"


def test_readiness_returns_503_when_database_is_unavailable(
    app: FastAPI, client: TestClient
) -> None:
    app.dependency_overrides[check_database] = lambda: DependencyCheck(
        name="database",
        status=DependencyStatus.UNAVAILABLE,
        detail="OperationalError",
    )
    try:
        response = client.get("/api/v1/health/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


def test_request_id_is_generated_and_returned(client: TestClient) -> None:
    response = client.get("/api/v1/health/live")

    request_id = response.headers[REQUEST_ID_HEADER]
    assert request_id


def test_incoming_request_id_is_reused(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={REQUEST_ID_HEADER: "abc-123"})

    assert response.headers[REQUEST_ID_HEADER] == "abc-123"


def test_unknown_route_uses_the_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"]
    assert body["error"]["request_id"]


def test_openapi_document_is_versioned(client: TestClient) -> None:
    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert paths
    versioned = [path for path in paths if path != "/"]
    assert versioned
    assert all(path.startswith("/api/v1") for path in versioned)


def test_root_exposes_service_metadata(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "multilingua-api"
    assert body["api_prefix"] == "/api/v1"
