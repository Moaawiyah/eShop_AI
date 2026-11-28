"""Key-based redaction of sensitive values for log output (SECURITY section 14).

A value is replaced when its key's lower-cased name contains a sensitive
marker. Nested mappings, lists and tuples are redacted recursively.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_MARKERS = (
    "password",
    "passwd",
    "secret",
    "token",
    "authorization",
    "cookie",
    "session",
    "csrf",
    "api_key",
    "apikey",
    "credential",
)


def is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in SENSITIVE_MARKERS)


def redact(value: Any) -> Any:
    """Redact sensitive keys in (nested) mappings and lists."""
    if isinstance(value, Mapping):
        return {str(k): REDACTED if is_sensitive(str(k)) else redact(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [redact(item) for item in value]
    return value
