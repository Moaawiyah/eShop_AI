"""Readiness holder state transitions."""

from __future__ import annotations

from app.core.readiness import Readiness


def test_starts_not_ready_and_toggles() -> None:
    readiness = Readiness()
    assert readiness.is_ready is False
    readiness.mark_ready()
    assert readiness.is_ready is True
    readiness.mark_not_ready()
    assert readiness.is_ready is False
