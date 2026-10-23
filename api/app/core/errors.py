"""Uniform API error contract.

All error responses share one shape so that clients never have to guess:

.. code-block:: json

    {
      "error": {
        "code": "not_found",
        "message": "Event not found.",
        "details": {"event_id": "..."},
        "request_id": "0f1e..."
      }
    }

``code`` is a stable machine readable identifier. ``message`` is a safe,
human readable summary that must never contain secrets or personal data.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    """Body of the ``error`` object."""

    code: str = Field(description="Stable machine readable error code.")
    message: str = Field(description="Safe, human readable summary.")
    details: dict[str, Any] | None = Field(default=None, description="Optional structured context.")
    request_id: str | None = Field(default=None, description="Correlation id of the request.")


class ErrorResponse(BaseModel):
    """Envelope returned for every non-2xx response."""

    error: ErrorPayload


class AppError(Exception):
    """Base class for expected, domain level failures."""

    status_code: int = 400
    code: str = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    """Raised when a requested resource does not exist or is not visible."""

    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    """Raised when a uniqueness or state constraint is violated."""

    status_code = 409
    code = "conflict"


class ValidationError(AppError):
    """Raised when input violates a domain rule that schema validation cannot express."""

    status_code = 422
    code = "validation_error"


class UnauthorizedError(AppError):
    """Raised when the caller is not authenticated."""

    status_code = 401
    code = "unauthorized"


class ForbiddenError(AppError):
    """Raised when the caller is authenticated but not allowed to perform the action."""

    status_code = 403
    code = "forbidden"
