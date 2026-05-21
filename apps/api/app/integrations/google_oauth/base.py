"""Protocol for Google OIDC metadata clients used by diagnostics."""

from typing import Any, Protocol


class GoogleOAuthClient(Protocol):
    @property
    def provider(self) -> str:
        """The selected Google OAuth provider mode for diagnostics."""

    async def discovery_document(self) -> dict[str, Any]:
        """Fetch an OpenID Connect discovery document."""

    async def jwks(self) -> dict[str, Any]:
        """Fetch a JSON Web Key Set."""
