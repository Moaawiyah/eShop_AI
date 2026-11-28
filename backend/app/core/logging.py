"""Structured logging configuration (NFR-OBS-001, SECURITY section 14).

JSON output has one object per line with the fields `timestamp`, `level`,
`service`, `logger`, `event` and `correlation_id` (always present, null
outside a request), plus any `extra=` keys that do not collide with those
core fields. Redaction (`app.core.redaction`) is applied here, not at call
sites. Exception messages are never written: only the exception type and the
stack frames (file, line, function).
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import UTC, datetime
from typing import Any

from app.core.context import get_request_id
from app.core.redaction import REDACTED, is_sensitive, redact

HANDLER_MARKER = "_eshop_log_handler"
_STANDARD_ATTRIBUTES = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "taskName",
    "color_message",  # uvicorn adds an ANSI-coloured duplicate of the message
}
# Core output fields: `extra=` can never override them.
RESERVED_FIELDS = frozenset(
    {
        "timestamp",
        "level",
        "service",
        "logger",
        "event",
        "correlation_id",
        "exc_type",
        "exc_frames",
    }
)


def extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    """Keys passed through `extra=`, redacted."""
    return {
        key: REDACTED if is_sensitive(key) else redact(value)
        for key, value in record.__dict__.items()
        if key not in _STANDARD_ATTRIBUTES
        and key not in RESERVED_FIELDS
        and not key.startswith("_")
    }


def safe_exception(record: logging.LogRecord) -> dict[str, Any]:
    """Exception type and frames only; the message may hold sensitive data."""
    if not record.exc_info or record.exc_info[1] is None:
        return {}
    exc = record.exc_info[1]
    frames = [
        f"{frame.filename}:{frame.lineno} in {frame.name}"
        for frame in traceback.extract_tb(exc.__traceback__)
    ]
    kind = type(exc)
    return {"exc_type": f"{kind.__module__}.{kind.__qualname__}", "exc_frames": frames}


def _timestamp(record: logging.LogRecord) -> str:
    moment = datetime.fromtimestamp(record.created, tz=UTC)
    return moment.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class JsonFormatter(logging.Formatter):
    """One JSON object per line."""

    def __init__(self, service_name: str = "eshop-backend") -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _timestamp(record),
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "event": record.getMessage(),
            "correlation_id": get_request_id(),
            **extra_fields(record),
            **safe_exception(record),
        }
        return json.dumps(payload, default=str, ensure_ascii=True)


class ConsoleFormatter(logging.Formatter):
    """Single human-readable line with the same redaction and exception policy."""

    def format(self, record: logging.LogRecord) -> str:
        parts = [
            _timestamp(record),
            f"{record.levelname:<7}",
            record.name,
            f"[{get_request_id() or '-'}]",
            record.getMessage(),
        ]
        parts.extend(
            f"{key}={value}"
            for key, value in {**extra_fields(record), **safe_exception(record)}.items()
        )
        return " ".join(parts)


def configure_logging(level: str, log_format: str, service_name: str = "eshop-backend") -> None:
    """Install exactly one marked stdout handler on the root logger (idempotent)."""
    root = logging.getLogger()
    formatter: logging.Formatter = (
        ConsoleFormatter() if log_format == "console" else JsonFormatter(service_name)
    )
    handler = next((h for h in root.handlers if getattr(h, HANDLER_MARKER, False)), None)
    if handler is None:
        handler = logging.StreamHandler(sys.stdout)
        setattr(handler, HANDLER_MARKER, True)
        root.addHandler(handler)
    handler.setFormatter(formatter)
    root.setLevel(level.upper())

    for name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    access = logging.getLogger("uvicorn.access")
    access.handlers.clear()
    access.propagate = False
    access.disabled = True
