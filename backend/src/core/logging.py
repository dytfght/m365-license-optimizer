"""
Structured JSON logging configuration using structlog
"""
import logging as stdlib_logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from .config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to all log messages.

    Args:
        logger: Logger instance
        method_name: Method name being called
        event_dict: Event dictionary

    Returns:
        Modified event dictionary with app context
    """
    event_dict["app_name"] = settings.APP_NAME
    event_dict["app_version"] = settings.APP_VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def configure_logging() -> None:
    """
    Configure structlog for JSON structured logging.

    This sets up:
    - JSON output format for production
    - Console output with colors for development
    - Request ID tracking
    - Timestamp in ISO format
    - Log level filtering based on settings
    """
    # Determine if we're in development mode
    is_dev = settings.ENVIRONMENT == "development"

    # Common processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    # Development: use colored console output
    if is_dev:
        processors = shared_processors + [structlog.dev.ConsoleRenderer(colors=True)]
    # Production: use JSON output
    else:
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            stdlib_logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    stdlib_logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=stdlib_logging.getLevelName(settings.LOG_LEVEL),
    )

    # Reduce noise from third-party libraries
    stdlib_logging.getLogger("uvicorn.access").setLevel(stdlib_logging.WARNING)
    stdlib_logging.getLogger("uvicorn.error").setLevel(stdlib_logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]
