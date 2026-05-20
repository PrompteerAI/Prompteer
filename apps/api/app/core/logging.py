"""Structured logging configuration shared by app, uvicorn, and SQLAlchemy logs."""

import logging
import sys

import structlog
from asgi_correlation_id import correlation_id

from app.core.config import settings


def add_request_id(
    _: object,
    __: str,
    event_dict: structlog.typing.EventDict,
) -> structlog.typing.EventDict:
    event_dict["request_id"] = event_dict.get("request_id") or correlation_id.get()
    event_dict["service"] = "prompteer-api"
    event_dict["version"] = settings.app_version
    event_dict["env"] = settings.env
    return event_dict


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    renderer: structlog.types.Processor
    if settings.log_json or settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    processor_formatter_processors: list[structlog.types.Processor] = [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
    ]
    if settings.log_json or settings.is_production:
        processor_formatter_processors.append(structlog.processors.dict_tracebacks)
    processor_formatter_processors.append(renderer)

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=processor_formatter_processors,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logging.disable(logging.NOTSET)
    root_logger = logging.getLogger()
    root_logger.disabled = False
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy"):
        named_logger = logging.getLogger(logger_name)
        named_logger.disabled = False
        named_logger.handlers.clear()
        named_logger.setLevel(logging.NOTSET)
        named_logger.propagate = True

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
