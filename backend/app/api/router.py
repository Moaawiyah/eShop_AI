"""Versioned API router assembly.

Module routers are included here as they are implemented. Health
endpoints are unversioned (ARCHITECTURE section 8) and exposed separately.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.config import router as config_router
from app.api.health import router as health_router

API_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_PREFIX)
api_router.include_router(config_router)


def unversioned_routers() -> list[APIRouter]:
    """Routers mounted without the API version prefix."""
    return [health_router]
