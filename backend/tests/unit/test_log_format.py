"""JSON/console formatters, redaction, exception policy and timestamps."""

from __future__ import annotations

import io
import json
import logging
import re

import pytest

from app.core.context import get_request_id, reset_request_id, set_request_id
from app.core.logging import ConsoleFormatter, JsonFormatter
from app.core.redaction import REDACTED

TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def make_logger(
    formatter: logging.Formatter, level: int = logging.DEBUG
) -> tuple[logging.Logger, io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger = logging.Logger("app.test", level)
    logger.addHandler(handler)
    return logger, stream


def test_json_line_has_required_fields() -> None:
    logger, stream = make_logger(JsonFormatter("svc"))
    logger.warning("hello %s", "world", extra={"method": "GET", "status_code": 200})
    lines = stream.getvalue().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert TIMESTAMP.match(entry["timestamp"])
    assert entry["level"] == "WARNING"
    assert entry["service"] == "svc"
    assert entry["logger"] == "app.test"
    assert entry["event"] == "hello world"
    assert entry["correlation_id"] is None
    assert (entry["method"], entry["status_code"]) == ("GET", 200)


def test_correlation_id_comes_from_context() -> None:
    logger, stream = make_logger(JsonFormatter())
    token = set_request_id("abcdefgh-1")
    try:
        logger.info("inside")
    finally:
        reset_request_id(token)
    logger.info("outside")
    inside, outside = (json.loads(line) for line in stream.getvalue().splitlines())
    assert inside["correlation_id"] == "abcdefgh-1"
    assert outside["correlation_id"] is None
    assert get_request_id() is None


def test_sensitive_extras_are_redacted_recursively() -> None:
    logger, stream = make_logger(JsonFormatter())
    logger.info(
        "x",
        extra={
            "password": "pw-value",
            "Authorization": "Bearer abc",
            "cookie": "sid=1",
            "session_id": "s1",
            "csrf_token": "c1",
            "API_KEY": "k1",
            "payload": {"user": "ann", "nested": {"client_secret": "s2", "ok": 1}},
            "items": [{"refresh_token": "t1"}],
        },
    )
    entry = json.loads(stream.getvalue())
    assert entry["password"] == entry["Authorization"] == entry["cookie"] == REDACTED
    assert entry["session_id"] == entry["csrf_token"] == entry["API_KEY"] == REDACTED
    assert entry["payload"] == {"user": "ann", "nested": {"client_secret": REDACTED, "ok": 1}}
    assert entry["items"] == [{"refresh_token": REDACTED}]
    for leaked in ("pw-value", "Bearer abc", "sid=1", "s1", "c1", "k1", "s2", "t1"):
        assert f'"{leaked}"' not in stream.getvalue()


@pytest.mark.parametrize("formatter", [JsonFormatter(), ConsoleFormatter()])
def test_exception_message_is_never_written(formatter: logging.Formatter) -> None:
    logger, stream = make_logger(formatter)
    try:
        raise ValueError("card 4111111111111111")
    except ValueError:
        logger.error("boom", exc_info=True)
    output = stream.getvalue()
    assert "4111111111111111" not in output
    assert "Traceback" not in output
    assert "builtins.ValueError" in output
    assert "test_exception_message_is_never_written" in output


def test_json_exception_fields() -> None:
    logger, stream = make_logger(JsonFormatter())
    try:
        raise KeyError("secret-key")
    except KeyError:
        logger.exception("failed")
    entry = json.loads(stream.getvalue())
    assert entry["exc_type"] == "builtins.KeyError"
    assert all(re.match(r".+:\d+ in \S+", frame) for frame in entry["exc_frames"])


@pytest.mark.parametrize("formatter", [JsonFormatter(), ConsoleFormatter()])
def test_extra_cannot_override_core_fields(formatter: logging.Formatter) -> None:
    logger, stream = make_logger(formatter)
    token = set_request_id("real-request-id")
    try:
        logger.info(
            "real event",
            extra={
                "correlation_id": "spoofed-id",
                "event": "spoofed event",
                "service": "spoofed-svc",
                "level": "CRITICAL",
                "logger": "spoofed.logger",
                "timestamp": "1970-01-01",
                "exc_type": "spoofed.Error",
            },
        )
    finally:
        reset_request_id(token)
    output = stream.getvalue()
    assert "spoofed" not in output
    assert "1970" not in output
    assert "real-request-id" in output
    assert "real event" in output


def test_uvicorn_color_message_is_not_logged() -> None:
    logger, stream = make_logger(JsonFormatter())
    logger.info("plain", extra={"color_message": "\x1b[36mcolored\x1b[0m"})
    assert "color_message" not in json.loads(stream.getvalue())


def test_console_format_line() -> None:
    logger, stream = make_logger(ConsoleFormatter())
    token = set_request_id("req-12345")
    try:
        logger.info("served", extra={"status_code": 204, "password": "p"})
    finally:
        reset_request_id(token)
    line = stream.getvalue().strip()
    assert "\n" not in line
    assert "INFO" in line
    assert "app.test" in line
    assert "[req-12345]" in line
    assert "served" in line
    assert f"status_code=204 password={REDACTED}" in line
