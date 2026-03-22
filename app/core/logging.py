"""
Structured JSON logging for production environments.

Outputs JSON in production for ELK / Kibana ingestion,
human-readable format in development.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Outputs log records as single-line JSON for ELK ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime, timezone

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure root logger based on the current environment."""
    root = logging.getLogger()
    root.setLevel(settings.app_log_level.upper())

    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if settings.is_production:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root.addHandler(handler)

    for noisy in ("uvicorn.access", "aiokafka", "aio_pika"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
