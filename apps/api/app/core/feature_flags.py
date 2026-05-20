from app.core.config import settings


def dev_routes_enabled() -> bool:
    return settings.enable_dev_routes and not settings.is_production
