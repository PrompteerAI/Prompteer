from app.core.config import settings


def init_observability() -> None:
    if settings.sentry_dsn:
        # Sentry is intentionally not imported until configured to keep local dev dependency-light.
        return
