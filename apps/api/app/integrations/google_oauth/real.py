"""Real Google OIDC metadata client for readiness and diagnostics."""

from typing import Any, cast

from app.integrations import http

GOOGLE_OIDC_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_TIMEOUT_SECONDS = 5.0


class RealGoogleOAuthClient:
    provider = "real"

    async def discovery_document(self) -> dict[str, Any]:
        response = await http.request(
            provider="google_oauth",
            method="GET",
            url=GOOGLE_OIDC_DISCOVERY_URL,
            timeout_seconds=GOOGLE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def jwks(self) -> dict[str, Any]:
        response = await http.request(
            provider="google_oauth",
            method="GET",
            url=GOOGLE_JWKS_URL,
            timeout_seconds=GOOGLE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())
