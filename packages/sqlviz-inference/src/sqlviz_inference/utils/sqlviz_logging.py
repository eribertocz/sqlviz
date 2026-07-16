"""Structured JSON logging for the SQLviz inference pipeline.

Usage:
    from sqlviz_inference.utils.sqlviz_logging import get_logger
    _log = get_logger("scoring_model")
    _log.warning("failed: %s", e, extra={"trace_id": context.trace_id})

Log level is controlled by the SQLVIZ_LOG_LEVEL environment variable
(default: WARNING). Set to DEBUG for verbose output during development.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        d: dict = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key in ("trace_id", "elapsed_ms", "execution_state", "error_count"):
            val = record.__dict__.get(key)
            if val is not None:
                d[key] = val
        return json.dumps(d, default=str)


_LEVEL_NAME = os.environ.get("SQLVIZ_LOG_LEVEL", "WARNING").upper()
_LEVEL = getattr(logging, _LEVEL_NAME, logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a structured JSON logger for a sqlviz module."""
    logger = logging.getLogger(f"sqlviz.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(_LEVEL)
        logger.propagate = False
    return logger
