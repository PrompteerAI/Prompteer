# Version 1 runtime configuration endpoints.

from fastapi import APIRouter

from app.core.config import settings
from app.core.feature_flags import feature_flags
from app.schemas.config import FeatureFlagsRead, IntegrationModesRead

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/features")
async def get_features() -> FeatureFlagsRead:
    return FeatureFlagsRead(**feature_flags())


@router.get("/integrations")
async def get_integration_modes() -> IntegrationModesRead:
    return IntegrationModesRead(
        google_oauth="real"
        if settings.google_client_id and settings.google_client_secret
        else "mock",
        llm="real" if settings.openai_api_key or settings.anthropic_api_key else "mock",
        payments="real" if settings.stripe_secret_key else "mock",
        email="real" if settings.sendgrid_api_key else "mock",
    )
