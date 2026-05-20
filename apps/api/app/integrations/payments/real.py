# Real Stripe Checkout client used when STRIPE_SECRET_KEY is configured.
# Form encoding mirrors Stripe's API while outbound calls share logging/retry behavior.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlencode

from app.integrations.http import RetryPolicy, request

STRIPE_READ_RETRY = RetryPolicy(max_attempts=3)


@dataclass(frozen=True)
class StripeClient:
    api_key: str
    base_url: str = "https://api.stripe.com"
    timeout_seconds: float = 20.0
    provider: str = "stripe"

    async def create_checkout_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_form("/v1/checkout/sessions", payload)

    async def retrieve_checkout_session(self, session_id: str) -> dict[str, Any]:
        response = await request(
            provider=self.provider,
            method="GET",
            url=f"{self.base_url.rstrip('/')}/v1/checkout/sessions/{session_id}",
            timeout_seconds=self.timeout_seconds,
            headers=self.headers(),
            retry_policy=STRIPE_READ_RETRY,
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise TypeError("Stripe Checkout Session response was not a JSON object.")
        return body

    async def expire_checkout_session(self, session_id: str) -> dict[str, Any]:
        return await self.post_form(f"/v1/checkout/sessions/{session_id}/expire", {})

    async def post_form(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        form_body = urlencode(cast(Any, list(flatten_form(payload))))
        response = await request(
            provider=self.provider,
            method="POST",
            url=f"{self.base_url.rstrip('/')}{path}",
            timeout_seconds=self.timeout_seconds,
            headers={
                **self.headers(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            content=form_body,
            request_body_for_logs=payload,
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise TypeError("Stripe response was not a JSON object.")
        return body

    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}


def flatten_form(value: Any, prefix: str | None = None) -> list[tuple[str, str]]:
    if isinstance(value, dict):
        pairs: list[tuple[str, str]] = []
        for key, item in value.items():
            next_prefix = key if prefix is None else f"{prefix}[{key}]"
            pairs.extend(flatten_form(item, next_prefix))
        return pairs
    if isinstance(value, list):
        pairs = []
        for index, item in enumerate(value):
            next_prefix = str(index) if prefix is None else f"{prefix}[{index}]"
            pairs.extend(flatten_form(item, next_prefix))
        return pairs
    if prefix is None or value is None:
        return []
    if isinstance(value, bool):
        return [(prefix, "true" if value else "false")]
    return [(prefix, str(value))]
