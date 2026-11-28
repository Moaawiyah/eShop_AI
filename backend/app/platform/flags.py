"""Typed, safe-by-default feature flags (FR-PLAT-013, ADR-0009).

Flags are evaluated on the server from typed settings. Only flags in
`PUBLIC_FLAGS` may be exposed to the frontend; every other flag stays on the
backend. A `context` argument for targeting is added when targeting exists.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from app.core.settings import Settings

logger = logging.getLogger(__name__)


class Flag(StrEnum):
    """Known flags; the value is the name used in APIs and logs."""

    AI_ASSISTANT = "ai_assistant"
    EXTERNAL_PRODUCT_SOURCES = "external_product_sources"
    NOTIFICATIONS = "notifications"


PUBLIC_FLAGS: frozenset[Flag] = frozenset({Flag.AI_ASSISTANT})


class FeatureFlags:
    """Read-only view of the feature flags configured in `Settings`."""

    def __init__(self, settings: Settings) -> None:
        self._values: dict[Flag, bool] = {
            flag: bool(getattr(settings, f"feature_{flag.value}")) for flag in Flag
        }
        logger.info("Feature flags loaded (enabled=%s)", self.enabled_names())

    def is_enabled(self, flag: Flag) -> bool:
        return self._values[flag]

    def public_flags(self) -> dict[str, bool]:
        """Allow-listed flags only; safe to send to the browser."""
        return {flag.value: self._values[flag] for flag in Flag if flag in PUBLIC_FLAGS}

    def enabled_names(self) -> list[str]:
        """Names of enabled flags (not sensitive), for the start-up log."""
        return [flag.value for flag in Flag if self._values[flag]]
