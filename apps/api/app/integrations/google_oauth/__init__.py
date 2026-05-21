"""Google OAuth client factory selecting real Google metadata or local mock OIDC."""

from app.core.config import google_oauth_integration_mode
from app.integrations.google_oauth.base import GoogleOAuthClient
from app.integrations.google_oauth.mock import MockGoogleOAuthClient
from app.integrations.google_oauth.real import RealGoogleOAuthClient


def get_google_oauth_client() -> GoogleOAuthClient:
    mode = google_oauth_integration_mode()
    if mode == "real":
        return RealGoogleOAuthClient()
    if mode == "partial":
        msg = "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set together."
        raise RuntimeError(msg)
    return MockGoogleOAuthClient()


__all__ = ["GoogleOAuthClient", "get_google_oauth_client"]
