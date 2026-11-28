"""Public configuration endpoints (ARCHITECTURE section 8).

Only intentionally public values are returned: the allow-listed feature
flags. Server-only flags and all other settings never leave the backend.
"""

from __future__ import annotations

from fastapi import APIRouter, Response
from pydantic import BaseModel, ConfigDict

from app.api.dependencies import FlagsDep

router = APIRouter(prefix="/config", tags=["config"])


class PublicFlagsResponse(BaseModel):
    """Must list exactly `PUBLIC_FLAGS` (checked by a test)."""

    model_config = ConfigDict(extra="forbid")

    ai_assistant: bool


@router.get(
    "/public-flags",
    operation_id="config_public_flags",
    summary="Public feature flags",
    response_model=PublicFlagsResponse,
)
async def public_flags(flags: FlagsDep, response: Response) -> PublicFlagsResponse:
    """Feature flags the frontend may read; all are off unless configured."""
    response.headers["Cache-Control"] = "no-store"
    return PublicFlagsResponse(**flags.public_flags())
