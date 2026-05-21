"""Real Google OIDC metadata client for readiness and diagnostics."""

from collections.abc import Mapping
from typing import Any, cast
from urllib.parse import urlencode

from app.integrations import http

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OIDC_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105  # Public OAuth endpoint.
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
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

    def authorization_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        response_type: str = "code",
        scope: str = "openid email profile",
        state: str | None = None,
        login_hint: str | None = None,
        nonce: str | None = None,
    ) -> str:
        query = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": response_type,
            "scope": scope,
        }
        if state is not None:
            query["state"] = state
        if login_hint is not None:
            query["login_hint"] = login_hint
        if nonce is not None:
            query["nonce"] = nonce
        return f"{GOOGLE_AUTHORIZATION_URL}?{urlencode(query)}"

    async def token(
        self,
        payload: Mapping[str, str],
        *,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        }
        if authorization is not None:
            headers["authorization"] = authorization
        response = await http.request(
            provider="google_oauth",
            method="POST",
            url=GOOGLE_TOKEN_URL,
            timeout_seconds=GOOGLE_TIMEOUT_SECONDS,
            headers=headers,
            content=urlencode(payload),
            request_body_for_logs=dict(payload),
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def userinfo(self, access_token: str) -> dict[str, Any]:
        response = await http.request(
            provider="google_oauth",
            method="GET",
            url=GOOGLE_USERINFO_URL,
            timeout_seconds=GOOGLE_TIMEOUT_SECONDS,
            headers={
                "accept": "application/json",
                "authorization": f"Bearer {access_token}",
            },
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())
