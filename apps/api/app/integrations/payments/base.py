"""Protocol for checkout and webhook-capable payment clients."""

from typing import Any, Protocol


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
