"""Unit tests for app.logging_config: JsonFormatter + configure_logging."""
from __future__ import annotations

import io
import json
import logging
from datetime import datetime

import pytest

from app.logging_config import JsonFormatter, configure_logging


@pytest.fixture
def reset_logging():
    """Reset the root logger between tests so configure_logging
    can re-fire idempotently.
    """
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.setLevel(logging.WARNING)
    # Force re-init on next call.
    import app.logging_config

    app.logging_config._CONFIGURED = False
    yield
    for h in list(root.handlers):
        root.removeHandler(h)
    app.logging_config._CONFIGURED = False


def test_json_formatter_emits_single_line_json(reset_logging):
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert parsed["msg"] == "hello world"
    assert "ts" in parsed
    # Parsed ISO timestamp
    datetime.fromisoformat(parsed["ts"])


def test_json_formatter_includes_extra_fields(reset_logging):
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="audit",
        level=logging.WARNING,
        pathname=__file__,
        lineno=20,
        msg="login failed",
        args=(),
        exc_info=None,
    )
    record.actor_id = 42  # type: ignore[attr-defined]
    record.ip = "127.0.0.1"  # type: ignore[attr-defined]
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["actor_id"] == 42
    assert parsed["ip"] == "127.0.0.1"


def test_json_formatter_includes_exception(reset_logging):
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="x",
            level=logging.ERROR,
            pathname=__file__,
            lineno=30,
            msg="oops",
            args=(),
            exc_info=sys.exc_info(),
        )
    parsed = json.loads(formatter.format(record))
    assert "exc" in parsed
    assert "ValueError" in parsed["exc"]
    assert "boom" in parsed["exc"]


def test_configure_logging_is_idempotent(reset_logging):
    configure_logging(level="INFO")
    h1 = logging.getLogger().handlers
    configure_logging(level="INFO")
    h2 = logging.getLogger().handlers
    assert h1 == h2


def test_configure_logging_text_format(reset_logging, monkeypatch):
    monkeypatch.setenv("CENIDIM_LOG_FORMAT", "text")
    configure_logging(level="INFO")
    root = logging.getLogger()
    assert any(isinstance(h.formatter, logging.Formatter) for h in root.handlers)
    # Verify the text format doesn't emit JSON.
    buffer = io.StringIO()
    test_handler = logging.StreamHandler(buffer)
    test_handler.setFormatter(root.handlers[0].formatter)
    record = logging.LogRecord(
        name="text.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=40,
        msg="plain",
        args=(),
        exc_info=None,
    )
    output = test_handler.format(record)
    assert "plain" in output
    assert not output.startswith("{")


def test_configure_logging_json_format_default(reset_logging, monkeypatch):
    monkeypatch.delenv("CENIDIM_LOG_FORMAT", raising=False)
    configure_logging(level="INFO")
    root = logging.getLogger()
    assert any(
        isinstance(h.formatter, JsonFormatter) for h in root.handlers
    )


def test_configure_logging_tames_noisy_loggers(reset_logging):
    configure_logging(level="INFO")
    for noisy in ("aiosqlite", "sqlalchemy.engine", "uvicorn.access"):
        assert logging.getLogger(noisy).level == logging.WARNING


def test_configure_logging_respects_level(reset_logging):
    configure_logging(level="WARNING")
    assert logging.getLogger().level == logging.WARNING
