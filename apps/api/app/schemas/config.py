# Public runtime configuration schemas returned by the versioned API.

from typing import Literal

from pydantic import BaseModel

IntegrationMode = Literal["mock", "real"]


class FeatureFlagsRead(BaseModel):
    llm: bool
    payments: bool
    email: bool


class IntegrationModesRead(BaseModel):
    google_oauth: IntegrationMode
    llm: IntegrationMode
    payments: IntegrationMode
    email: IntegrationMode
