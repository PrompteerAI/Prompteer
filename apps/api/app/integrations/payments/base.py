"""Protocol for checkout and webhook-capable payment clients."""

from __future__ import annotations

from typing import Any, Protocol


class PaymentsProviderError(Exception):
    """Safe, user-facing wrapper for live payments provider failures."""

    def __init__(
        self,
        *,
        provider: str,
        detail: str,
        status_code: int | None = None,
    ) -> None:
        super().__init__(detail)
        self.provider = provider
        self.detail = detail
        self.status_code = status_code


class PaymentsClient(Protocol):
    @property
    def provider(self) -> str:
        """The selected payments provider name for boot logs and diagnostics."""

    async def create_checkout_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a Stripe Checkout Session compatible response."""

    async def retrieve_checkout_session(self, session_id: str) -> dict[str, Any]:
        """Retrieve a Stripe Checkout Session compatible response."""

    async def expire_checkout_session(self, session_id: str) -> dict[str, Any]:
        """Expire a Stripe Checkout Session compatible response."""
