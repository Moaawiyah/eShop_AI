"""Unversioned, public liveness and readiness endpoints (ARCHITECTURE section 8).

Known limitation: Uvicorn stops accepting new connections when shutdown
starts and runs the lifespan shutdown after in-flight requests finish, so
within one process the 503 during shutdown only reaches in-flight or
keep-alive requests; it matters mainly to orchestrator probes (M8).
Database and Redis readiness checks arrive in M2, Watchdog checks in M8.
Bodies deliberately contain only `status`: no version, host or config.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel, ConfigDict

from app.core.readiness import Readiness

router = APIRouter(prefix="/health", tags=["health"])

NO_STORE = "no-store"


class LivenessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "not_ready"]


@router.get(
    "/live",
    operation_id="health_live",
    summary="Liveness probe",
    response_model=LivenessResponse,
)
async def live(response: Response) -> LivenessResponse:
    """The process is running; independent of every dependency."""
    response.headers["Cache-Control"] = NO_STORE
    return LivenessResponse(status="ok")


@router.get(
    "/ready",
    operation_id="health_ready",
    summary="Readiness probe",
    response_model=ReadinessResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadinessResponse,
            "description": "Not started yet or shutting down.",
        }
    },
)
async def ready(request: Request, response: Response) -> ReadinessResponse:
    """200 once start-up has finished; 503 before that and during shutdown."""
    response.headers["Cache-Control"] = NO_STORE
    readiness: Readiness = request.app.state.readiness
    if readiness.is_ready:
        return ReadinessResponse(status="ready")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="not_ready")
