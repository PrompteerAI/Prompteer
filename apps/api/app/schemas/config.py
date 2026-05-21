# Public runtime configuration schemas returned by the versioned API.

from pydantic import BaseModel

from app.core.config import GoogleOAuthIntegrationMode, RealMockIntegrationMode


class FeatureFlagsRead(BaseModel):
    llm: bool
    payments: bool
    email: bool


class IntegrationModesRead(BaseModel):
    google_oauth: GoogleOAuthIntegrationMode
    llm: RealMockIntegrationMode
    payments: RealMockIntegrationMode
    email: RealMockIntegrationMode
