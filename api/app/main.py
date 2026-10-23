"""FastAPI application factory.

The factory pattern keeps the application constructible in tests with
explicit settings, and avoids import-time side effects beyond creating the
application object itself.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app import __version__
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.event_loop import install_event_loop_policy
from app.core.logging import configure_logging, get_logger
from app.core.middleware import REQUEST_ID_HEADER, RequestContextMiddleware

# Must run before the first event loop is created (see app.core.event_loop).
install_event_loop_policy()

_logger = get_logger("api")

API_PREFIX = "/api/v1"


def _request_id(request: Request) -> str | None:
    state = getattr(request.state, "request_id", None)
    return cast("str | None", state)


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": _request_id(request),
        }
    }
    return JSONResponse(status_code=status_code, content=payload)


async def _handle_app_error(request: Request, exc: Exception) -> Response:
    error = cast("AppError", exc)
    return _error_response(
        request,
        error.status_code,
        error.code,
        error.message,
        error.details,
    )


async def _handle_validation_error(request: Request, exc: Exception) -> Response:
    validation_error = cast("RequestValidationError", exc)
    fields = [
        {
            "location": [str(part) for part in error.get("loc", ())],
            "message": str(error.get("msg", "invalid value")),
            "type": str(error.get("type", "value_error")),
        }
        for error in validation_error.errors()
    ]
    return _error_response(
        request,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation_error",
        "Request validation failed.",
        {"fields": fields},
    )


async def _handle_http_exception(request: Request, exc: Exception) -> Response:
    http_exception = cast("StarletteHTTPException", exc)
    code = "not_found" if http_exception.status_code == status.HTTP_404_NOT_FOUND else "http_error"
    message = str(http_exception.detail) if http_exception.detail else "Request failed."
    return _error_response(request, http_exception.status_code, code, message)


async def _handle_unexpected_error(request: Request, exc: Exception) -> Response:
    _logger.exception("unhandled_error", error_type=type(exc).__name__)
    return _error_response(
        request,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "An unexpected error occurred.",
    )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _logger.info(
        "service_started",
        app_env=settings.app_env,
        version=__version__,
        api_prefix=API_PREFIX,
    )
    try:
        yield
    finally:
        _logger.info("service_stopped", version=__version__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application."""
    resolved = settings or get_settings()
    configure_logging(resolved.log_level)

    app = FastAPI(
        title="Multilingual Event Platform API",
        version=__version__,
        description=(
            "Backend for the multilingual event platform. "
            "Public routes are served from the same application under "
            "`/api/v1/public`."
        ),
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
        max_age=600,
    )
    app.add_middleware(RequestContextMiddleware)

    app.add_exception_handler(AppError, _handle_app_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(Exception, _handle_unexpected_error)

    app.include_router(api_router, prefix=API_PREFIX)

    @app.get("/", tags=["meta"], summary="Service metadata")
    async def root() -> dict[str, str]:
        return {
            "service": "multilingua-api",
            "version": __version__,
            "api_prefix": API_PREFIX,
            "docs": f"{API_PREFIX}/docs",
        }

    return app


app = create_app()
