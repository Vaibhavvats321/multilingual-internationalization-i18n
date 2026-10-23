"""Core cross-cutting concerns: configuration, logging, errors, middleware."""

from app.core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
