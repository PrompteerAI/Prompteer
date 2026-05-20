# Version 1 runtime configuration endpoints.

from fastapi import APIRouter

from app.core.feature_flags import feature_flags
from app.schemas.config import FeatureFlagsRead

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/features")
async def get_features() -> FeatureFlagsRead:
    return FeatureFlagsRead(**feature_flags())
