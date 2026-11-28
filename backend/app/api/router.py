"""Versioned API router assembly.

Module routers are included here as they are implemented; the first
endpoints (health checks) arrive in SHOP-013.
"""

from __future__ import annotations

from fastapi import APIRouter

API_PREFIX = "/api/v1"

api_router = APIRouter(prefix=API_PREFIX)
