"""API v1 runtime configuration routes; no sibling config API version exists yet."""

from fastapi import APIRouter

from app.core.config import integration_modes
from app.core.feature_flags import feature_flags
from app.schemas.config import FeatureFlagsRead, IntegrationModesRead

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/features")
async def get_features() -> FeatureFlagsRead:
    return FeatureFlagsRead(**feature_flags())


@router.get("/integrations")
async def get_integration_modes() -> IntegrationModesRead:
    modes = integration_modes()
    return IntegrationModesRead(
        google_oauth=modes["google_oauth"],
        llm=modes["llm"],
        payments=modes["stripe"],
        email=modes["email"],
    )
