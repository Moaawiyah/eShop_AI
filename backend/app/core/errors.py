"""Common application error type (ARCHITECTURE section 3.8).

Domain errors derive from `AppError`; the API layer maps them centrally to
RFC 9457 problem details. `detail` must be safe to show to customers.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for errors that map to a specific HTTP problem response."""

    status_code: int = 500
    code: str = "internal_error"
    title: str = "Internal Server Error"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.title)
        self.detail = detail
