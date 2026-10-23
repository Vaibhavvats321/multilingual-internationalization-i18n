"""Pure ASGI middleware: correlation ids and access logging.

Implemented as raw ASGI (rather than ``BaseHTTPMiddleware``) so that the
request id is bound in the same task that runs the endpoint. Context variables
set here are therefore visible to every log line emitted while handling the
request, including those from inside the route handler.
"""

from __future__ import annotations

from uuid import uuid4

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger

REQUEST_ID_HEADER = "X-Request-ID"

_logger = get_logger("api.access")


class RequestContextMiddleware:
    """Attach a request id to every request/response pair and log the outcome."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        incoming = headers.get(REQUEST_ID_HEADER)
        request_id = incoming.strip()[:128] if incoming and incoming.strip() else uuid4().hex

        scope.setdefault("state", {})["request_id"] = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            structlog.contextvars.clear_contextvars()
