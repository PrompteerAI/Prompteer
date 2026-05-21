"""Protocol for Google OIDC metadata clients used by diagnostics."""

from collections.abc import Mapping
from typing import Any, Protocol


class GoogleOAuthClient(Protocol):
    @property
    def provider(self) -> str:
        """The selected Google OAuth provider mode for diagnostics."""

    async def discovery_document(self) -> dict[str, Any]:
        """Fetch an OpenID Connect discovery document."""

    async def jwks(self) -> dict[str, Any]:
        """Fetch a JSON Web Key Set."""

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
        """Build an OAuth authorization URL."""

    async def token(
        self,
        payload: Mapping[str, str],
        *,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        """Exchange an authorization code for OAuth tokens."""

    async def userinfo(self, access_token: str) -> dict[str, Any]:
        """Fetch the OpenID Connect userinfo document."""
