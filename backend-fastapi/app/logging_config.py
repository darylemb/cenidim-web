"""Structured JSON logging.

Production logs need to be machine-parseable; the Coolify / Grafana
stack ingests JSON via Promtail. ``configure_logging(level)`` sets
up a single ``logging.StreamHandler`` with a JSON formatter that
emits one record per line including timestamp, level, logger, msg,
plus any ``extra=`` fields the call site added.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit each LogRecord as a single-line JSON object."""

    # LogRecord attributes we never want to surface in the JSON payload.
    _SKIP = frozenset(
        {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "asctime",
            "taskName",
        }
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # ``extra=`` fields propagate as attributes on the record.
        for key, value in record.__dict__.items():
            if key in self._SKIP or key.startswith("_"):
                continue
            payload[key] = value
        return json.dumps(payload, default=str, ensure_ascii=False)


_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Idempotent root-logger configuration.

    Production (Coolify / docker) wants JSON for Promtail / Grafana;
    dev defaults to a human-readable format. We pick the format
    based on the ``CENIDIM_LOG_FORMAT`` env var (default ``json``).
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(stream=sys.stdout)
    fmt_env = (os.environ.get("CENIDIM_LOG_FORMAT") or "json").lower()
    if fmt_env == "text":
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )
    else:
        handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    # Wipe any existing handlers so test re-configurations don't pile up.
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Tame the chatty third-party loggers.
    for noisy in (
        "uvicorn.access",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "aiosqlite",
        "multipart",
    ):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


__all__ = ["JsonFormatter", "configure_logging"]
