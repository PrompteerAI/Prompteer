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
    event_dict["request_id"] = correlation_id.get()
    event_dict["service"] = "prompteer-api"
    event_dict["env"] = settings.env
    return event_dict


def configure_logging() -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    renderer: structlog.types.Processor
    if settings.log_json or settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.format_exc_info,
        renderer,
    ]

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
