"""Stripe webhook signature helpers shared by real and mock payment flows."""

from __future__ import annotations

import hmac
import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from app.core.config import settings

# Local-only mock signing secret; real mode reads STRIPE_WEBHOOK_SECRET.
MOCK_STRIPE_WEBHOOK_SECRET = "whsec_mock_prompteer"  # noqa: S105  # Local-only test secret.


class StripeWebhookSignatureError(ValueError):
    """Raised when a Stripe webhook payload cannot be trusted."""


def stripe_webhook_secret() -> str:
    if settings.stripe_webhook_secret:
        return settings.stripe_webhook_secret
    if settings.stripe_secret_key:
        raise StripeWebhookSignatureError(
            "STRIPE_WEBHOOK_SECRET is required when STRIPE_SECRET_KEY is set."
        )
    return MOCK_STRIPE_WEBHOOK_SECRET


def sign_stripe_webhook_payload(
    payload: str,
    secret: str | None = None,
    *,
    timestamp: int | None = None,
) -> str:
    timestamp = timestamp if timestamp is not None else int(datetime.now(tz=UTC).timestamp())
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        (secret or stripe_webhook_secret()).encode(), signed_payload.encode(), sha256
    )
    return f"t={timestamp},v1={signature.hexdigest()}"


def construct_stripe_event(
    payload: str,
    signature_header: str,
    secret: str | None = None,
) -> dict[str, Any]:
    verify_stripe_webhook_signature(payload, signature_header, secret or stripe_webhook_secret())
    try:
        event = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise StripeWebhookSignatureError("Webhook payload must be valid JSON.") from exc
    if not isinstance(event, dict):
        raise StripeWebhookSignatureError("Webhook payload must decode to an object.")
    validate_stripe_event_shape(event)
    return event


def validate_stripe_event_shape(event: dict[str, Any]) -> None:
    if event.get("object") != "event":
        raise StripeWebhookSignatureError("Webhook payload is not a Stripe event.")
    if not isinstance(event.get("id"), str) or not event["id"]:
        raise StripeWebhookSignatureError("Stripe event id is missing.")
    if not isinstance(event.get("type"), str) or not event["type"]:
        raise StripeWebhookSignatureError("Stripe event type is missing.")
    data = event.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("object"), dict):
        raise StripeWebhookSignatureError("Stripe event data.object is missing.")


def verify_stripe_webhook_signature(
    payload: str,
    signature_header: str,
    secret: str,
    *,
    tolerance_seconds: int = 300,
) -> None:
    values = parse_signature_header(signature_header)
    timestamp = values.get("t")
    signatures = values.get("v1", [])
    if not isinstance(timestamp, str) or not isinstance(signatures, list):
        raise StripeWebhookSignatureError("Stripe-Signature header is missing t or v1.")
    signed_payload = f"{timestamp}.{payload}"
    expected = hmac.new(secret.encode(), signed_payload.encode(), sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
        raise StripeWebhookSignatureError("No matching Stripe webhook signature.")
    try:
        age = abs(int(datetime.now(tz=UTC).timestamp()) - int(timestamp))
    except ValueError as exc:
        raise StripeWebhookSignatureError("Stripe webhook signature timestamp is invalid.") from exc
    if age > tolerance_seconds:
        raise StripeWebhookSignatureError(
            "Stripe webhook signature timestamp is outside tolerance."
        )


def parse_signature_header(header: str) -> dict[str, str | list[str]]:
    values: dict[str, str | list[str]] = {}
    for part in header.split(","):
        key, separator, value = part.partition("=")
        key = key.strip()
        value = value.strip()
        if separator == "":
            continue
        if key == "v1":
            values.setdefault("v1", [])
            v1_values = values["v1"]
            if isinstance(v1_values, list):
                v1_values.append(value)
        else:
            values[key] = value
    return values
