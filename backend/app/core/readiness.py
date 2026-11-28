"""Readiness state holder (ARCHITECTURE sections 3.6 and 8)."""

from __future__ import annotations


class Readiness:
    """Whether the application accepts traffic; starts not ready.

    Only start-up completion is tracked today. Database and Redis checks
    arrive in M2 and Watchdog-based checks in M8.
    """

    def __init__(self) -> None:
        self._ready = False

    @property
    def is_ready(self) -> bool:
        return self._ready

    def mark_ready(self) -> None:
        self._ready = True

    def mark_not_ready(self) -> None:
        self._ready = False
