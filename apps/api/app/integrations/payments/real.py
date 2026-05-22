# Real Stripe Checkout client used when STRIPE_SECRET_KEY is configured.
# Form encoding mirrors Stripe's API while outbound calls share logging/retry behavior.

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlencode

import httpx

from app.integrations.http import RetryPolicy, request
from app.integrations.payments.base import PaymentsProviderError

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
        try:
            response = await request(
                provider=self.provider,
                method="GET",
                url=f"{self.base_url.rstrip('/')}/v1/checkout/sessions/{session_id}",
                timeout_seconds=self.timeout_seconds,
                headers=self.headers(),
                retry_policy=STRIPE_READ_RETRY,
            )
            return stripe_response_body(
                self.provider,
                response,
                not_object_detail="Stripe Checkout Session response was not a JSON object.",
            )
        except httpx.HTTPStatusError as exc:
            raise stripe_provider_http_error(self.provider, exc.response) from exc
        except (httpx.TransportError, TypeError, ValueError) as exc:
            raise PaymentsProviderError(
                provider=self.provider,
                detail=f"{self.provider} provider is unavailable.",
            ) from exc

    async def expire_checkout_session(self, session_id: str) -> dict[str, Any]:
        return await self.post_form(f"/v1/checkout/sessions/{session_id}/expire", {})

    async def post_form(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        form_body = urlencode(cast(Any, list(flatten_form(payload))))
        try:
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
            return stripe_response_body(
                self.provider,
                response,
                not_object_detail="Stripe response was not a JSON object.",
            )
        except httpx.HTTPStatusError as exc:
            raise stripe_provider_http_error(self.provider, exc.response) from exc
        except (httpx.TransportError, TypeError, ValueError) as exc:
            raise PaymentsProviderError(
                provider=self.provider,
                detail=f"{self.provider} provider is unavailable.",
            ) from exc

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


def stripe_response_body(
    provider: str,
    response: httpx.Response,
    *,
    not_object_detail: str,
) -> dict[str, Any]:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise stripe_provider_http_error(provider, exc.response) from exc
    body = response.json()
    if not isinstance(body, dict):
        raise TypeError(not_object_detail)
    return body


def stripe_provider_http_error(provider: str, response: httpx.Response) -> PaymentsProviderError:
    provider_message = stripe_error_message(response)
    detail = f"{provider} provider returned HTTP {response.status_code}."
    if provider_message:
        detail = f"{detail} {provider_message}"
    return PaymentsProviderError(provider=provider, detail=detail, status_code=response.status_code)


def stripe_error_message(response: httpx.Response) -> str | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                return message
        message = body.get("message")
        if isinstance(message, str):
            return message
    return None
