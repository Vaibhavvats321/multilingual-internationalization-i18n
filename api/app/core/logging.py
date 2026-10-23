"""Structured logging setup.

Every log line is emitted as JSON so that it can be shipped and queried
without a parsing layer. The standard library logger (used by uvicorn) is
routed through the same formatter, which keeps access logs and application
logs in one format.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

#: Processors shared by the structlog logger and by foreign (stdlib) records.
_SHARED_PROCESSORS: list[Any] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]


def configure_logging(level: str = "info") -> None:
    """Configure structlog and the standard library root logger."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            *_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_SHARED_PROCESSORS,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).propagate = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)  # type: ignore[no-any-return]


def redact(message: str, *secrets: str | None) -> str:
    """Remove sensitive values from a message before it is logged.

    Database drivers and HTTP libraries occasionally echo the connection
    string or a credential back in an error message. Every value that must
    never reach the log is passed in ``secrets`` and replaced by ``***``.
    """
    for secret in secrets:
        if secret:
            message = message.replace(secret, "***")
    return message
