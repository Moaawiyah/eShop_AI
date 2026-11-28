"""Request-scoped context shared by logging and the API layer.

A `ContextVar` is isolated per asyncio task, so concurrent requests never
see each other's request ID.
"""

from __future__ import annotations

from contextvars import ContextVar, Token

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Return the current request ID, or None outside a request."""
    return _request_id.get()


def set_request_id(value: str) -> Token[str | None]:
    """Set the request ID; pass the returned token to `reset_request_id`."""
    return _request_id.set(value)


def reset_request_id(token: Token[str | None]) -> None:
    """Restore the value that was active before `set_request_id`."""
    _request_id.reset(token)
