from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        record.trace_id = trace_id_var.get("-")
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s | %(levelname)s | %(name)s | trace_id=%(trace_id)s | %(message)s"
        ),
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    root_logger = logging.getLogger()
    root_logger.addFilter(TraceIdFilter())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def generate_trace_id() -> str:
    return uuid.uuid4().hex


def get_trace_id() -> str:
    return trace_id_var.get("-")


def set_trace_id(trace_id: str) -> None:
    trace_id_var.set(trace_id)
