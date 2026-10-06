import logging
import sys

import structlog
from structlog.typing import EventDict, WrappedLogger

from fea_core.telemetry import add_trace_context

PII_KEYS = frozenset(
    {
        "email",
        "name",
        "phone",
        "address",
        "password",
        "token",
        "access_token",
        "authorization",
        "sub",
    }
)
REDACTED = "[redacted]"


def redact_pii(_logger: WrappedLogger, _method: str, event_dict: EventDict) -> EventDict:
    for key in PII_KEYS & event_dict.keys():
        event_dict[key] = REDACTED
    return event_dict


def configure_logging(level: str) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            add_trace_context,
            redact_pii,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level.upper())),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )
