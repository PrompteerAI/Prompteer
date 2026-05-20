# Environment-backed feature kill switches. These are intentionally simple:
# they protect cost-sensitive integrations without introducing a flag service.

from typing import Literal

from starlette import status

from app.core.config import settings
from app.core.errors import ProblemException

FeatureName = Literal["llm", "payments", "email"]

FEATURE_SETTINGS: dict[FeatureName, str] = {
    "llm": "feature_llm_enabled",
    "payments": "feature_payments_enabled",
    "email": "feature_email_enabled",
}

FEATURE_LABELS: dict[FeatureName, str] = {
    "llm": "LLM prompt runs",
    "payments": "Payments",
    "email": "Email delivery",
}


def dev_routes_enabled() -> bool:
    return settings.enable_dev_routes and not settings.is_production


def feature_flags() -> dict[FeatureName, bool]:
    return {
        "llm": settings.feature_llm_enabled,
        "payments": settings.feature_payments_enabled,
        "email": settings.feature_email_enabled,
    }


def feature_enabled(feature: FeatureName) -> bool:
    return bool(getattr(settings, FEATURE_SETTINGS[feature]))


def require_feature_enabled(feature: FeatureName) -> None:
    if feature_enabled(feature):
        return
    raise ProblemException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        title="Feature Disabled",
        detail=f"{FEATURE_LABELS[feature]} are currently disabled.",
        code="feature_disabled",
    )
