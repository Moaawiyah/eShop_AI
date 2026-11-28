"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.platform.flags import FeatureFlags


def get_flags(request: Request) -> FeatureFlags:
    """The application's feature flags (created in `create_app`)."""
    flags: FeatureFlags = request.app.state.flags
    return flags


FlagsDep = Annotated[FeatureFlags, Depends(get_flags)]
