# Public runtime configuration schemas returned by the versioned API.

from pydantic import BaseModel


class FeatureFlagsRead(BaseModel):
    llm: bool
    payments: bool
    email: bool
