"""FastAPI application factory and lifespan (ARCHITECTURE sections 3.1 and 3.6)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.errors import register_error_handlers
from app.api.middleware import RequestContextMiddleware
from app.api.router import API_PREFIX, api_router, unversioned_routers
from app.core.logging import configure_logging
from app.core.readiness import Readiness
from app.core.settings import Settings, get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create long-lived components on start-up and release them on shutdown.

    Uvicorn stops accepting connections and waits for in-flight requests
    (up to SHUTDOWN_TIMEOUT_SECONDS) before this context exits.
    """
    settings: Settings = app.state.settings
    readiness: Readiness = app.state.readiness
    logger.info("Backend starting (environment=%s)", settings.app_env)
    readiness.mark_ready()
    logger.info("Readiness established")
    try:
        yield
    finally:
        readiness.mark_not_ready()
        logger.info("Readiness withdrawn")
        logger.info("Backend shutting down")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the application; tests pass their own settings."""
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)
    docs = settings.api_docs_enabled
    app = FastAPI(
        title="eShop_AI API",
        version="0.1.0",
        debug=settings.app_debug,
        lifespan=lifespan,
        openapi_url=f"{API_PREFIX}/openapi.json" if docs else None,
        docs_url=f"{API_PREFIX}/docs" if docs else None,
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.readiness = Readiness()
    register_error_handlers(app)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(api_router)
    for router in unversioned_routers():
        app.include_router(router)
    return app
