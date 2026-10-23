"""Versioned API router assembly.

Every route is mounted under ``/api/v1`` (see ``app.main``) so that a future
breaking version can be introduced alongside the current one.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)
