"""configure_logging, handler routing, levels, repeated create_app and settings."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pytest
from pydantic import ValidationError

from app.core.logging import HANDLER_MARKER, ConsoleFormatter, JsonFormatter, configure_logging
from app.core.settings import Settings
from app.main import create_app


def marked_handlers() -> list[logging.Handler]:
    return [h for h in logging.getLogger().handlers if getattr(h, HANDLER_MARKER, False)]


def test_configure_logging_is_idempotent_and_keeps_foreign_handlers() -> None:
    foreign = logging.NullHandler()
    logging.getLogger().addHandler(foreign)
    try:
        for _ in range(3):
            configure_logging("INFO", "json")
        assert len(marked_handlers()) == 1
        assert foreign in logging.getLogger().handlers
    finally:
        logging.getLogger().removeHandler(foreign)


def test_configure_logging_switches_format() -> None:
    configure_logging("INFO", "json")
    assert isinstance(marked_handlers()[0].formatter, JsonFormatter)
    configure_logging("INFO", "console")
    assert len(marked_handlers()) == 1
    assert isinstance(marked_handlers()[0].formatter, ConsoleFormatter)


def test_configure_logging_routes_uvicorn_loggers() -> None:
    logging.getLogger("uvicorn").addHandler(logging.NullHandler())
    configure_logging("INFO", "json")
    assert logging.getLogger("uvicorn").handlers == []
    assert logging.getLogger("uvicorn").propagate is True
    assert logging.getLogger("uvicorn.error").propagate is True
    access = logging.getLogger("uvicorn.access")
    assert access.propagate is False
    assert access.disabled is True


def test_level_filters_debug_but_shows_it_when_enabled(capsys: pytest.CaptureFixture[str]) -> None:
    logger = logging.getLogger("app.level_test")
    configure_logging("INFO", "json")
    logger.debug("hidden-debug")
    logger.info("shown-info")
    configure_logging("debug", "json")
    logger.debug("shown-debug")
    out = capsys.readouterr().out
    assert "hidden-debug" not in out
    assert "shown-info" in out
    assert "shown-debug" in out


def test_repeated_create_app_writes_one_line_per_record(
    make_settings: Callable[..., Settings], capsys: pytest.CaptureFixture[str]
) -> None:
    for _ in range(3):
        create_app(make_settings())
    logging.getLogger("app.once").info("only-once")
    assert capsys.readouterr().out.count("only-once") == 1
    assert len(marked_handlers()) == 1


def test_settings_log_options(make_settings: Callable[..., Settings]) -> None:
    assert make_settings().log_level == "INFO"
    assert make_settings().log_format == "json"
    assert make_settings(log_level="debug", log_format="CONSOLE").log_level == "DEBUG"
    assert make_settings(log_format="CONSOLE").log_format == "console"


@pytest.mark.parametrize(("field", "value"), [("log_level", "TRACE"), ("log_format", "xml")])
def test_invalid_log_settings_rejected(
    make_settings: Callable[..., Settings], field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        make_settings(**{field: value})
