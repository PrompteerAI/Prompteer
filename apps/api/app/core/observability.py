# Optional Sentry initialization and capture helpers for the FastAPI service.
# The SDK stays disabled in local development unless SENTRY_DSN is configured.

from typing import Protocol, cast

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class SentryModule(Protocol):
    def init(self, **kwargs: object) -> object: ...

    def capture_exception(self, error: BaseException) -> object: ...

    def set_tag(self, key: str, value: str) -> None: ...


def init_observability() -> None:
    if not settings.sentry_dsn:
        logger.info("sentry_disabled")
        return

    sentry_sdk = import_sentry_sdk()
    fastapi_integration = import_fastapi_integration()
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.env,
        release=settings.app_version,
        integrations=[fastapi_integration],
        send_default_pii=False,
        traces_sample_rate=0.1 if settings.is_production else 1.0,
        enable_logs=True,
    )
    sentry_sdk.set_tag("service", "prompteer-api")
    sentry_sdk.set_tag("version", settings.app_version)
    logger.info("sentry_enabled")


def capture_exception(error: BaseException) -> None:
    if not settings.sentry_dsn:
        return
    import_sentry_sdk().capture_exception(error)


def import_sentry_sdk() -> SentryModule:
    import sentry_sdk

    return cast(SentryModule, sentry_sdk)


def import_fastapi_integration() -> object:
    from sentry_sdk.integrations.fastapi import FastApiIntegration

    return FastApiIntegration()
