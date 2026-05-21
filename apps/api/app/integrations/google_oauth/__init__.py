"""Google OAuth client factory selecting real Google metadata or local mock OIDC."""

from app.core.config import settings
from app.integrations.google_oauth.base import GoogleOAuthClient
from app.integrations.google_oauth.mock import MockGoogleOAuthClient
from app.integrations.google_oauth.real import RealGoogleOAuthClient


def get_google_oauth_client() -> GoogleOAuthClient:
    if settings.google_client_id and settings.google_client_secret:
        return RealGoogleOAuthClient()
    return MockGoogleOAuthClient()


__all__ = ["GoogleOAuthClient", "get_google_oauth_client"]
