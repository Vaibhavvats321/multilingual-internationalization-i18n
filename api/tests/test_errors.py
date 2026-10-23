"""Tests for the shared error contract."""

from __future__ import annotations

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.core.errors import AppError, ConflictError, NotFoundError


@pytest.fixture
def error_app(app: FastAPI) -> FastAPI:
    router = APIRouter()

    @router.get("/boom")
    async def boom() -> None:
        raise NotFoundError("Event not found.", details={"event_id": "evt_1"})

    @router.get("/conflict")
    async def conflict() -> None:
        raise ConflictError("Slug already taken.")

    @router.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("boom")

    app.include_router(router)
    return app


def test_app_error_is_rendered_with_the_standard_envelope(error_app: FastAPI) -> None:
    with TestClient(error_app) as client:
        response = client.get("/boom")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Event not found."
    assert body["error"]["details"] == {"event_id": "evt_1"}


def test_conflict_error_uses_http_409(error_app: FastAPI) -> None:
    with TestClient(error_app) as client:
        response = client.get("/conflict")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_unexpected_errors_do_not_leak_internals(error_app: FastAPI) -> None:
    with TestClient(error_app, raise_server_exceptions=False) as client:
        response = client.get("/unexpected")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert "boom" not in body["error"]["message"]


def test_app_error_defaults() -> None:
    error = AppError("Something went wrong.")

    assert error.status_code == 400
    assert error.code == "bad_request"
    assert error.details is None
