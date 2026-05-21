"""Stripe Checkout mock.

Schema references verified on 2026-05-21:
- https://docs.stripe.com/api/checkout/sessions
- https://docs.stripe.com/api/checkout/sessions/create
- https://docs.stripe.com/api/checkout/sessions/retrieve
- https://docs.stripe.com/api/checkout/sessions/expire
- https://docs.stripe.com/webhooks/signature
"""

from __future__ import annotations

import json
import re
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from app.core.feature_flags import dev_routes_enabled, require_feature_enabled
from app.core.ratelimit import PAYMENTS_RATE_LIMIT, limiter
from app.integrations.payments.webhooks import (
    StripeWebhookSignatureError,
    construct_stripe_event,
    sign_stripe_webhook_payload,
    stripe_webhook_secret,
)

MOCK_CHECKOUT_BASE_URL = "https://checkout.stripe.com/c/pay"
SEED_CHECKOUT_CREATED = 1_800_000_000
FORM_KEY_PATTERN = re.compile(r"[^\[\]]+")

router = APIRouter(tags=["mock-stripe"])


class MockStripeError(ValueError):
    pass


MockStripeSignatureError = StripeWebhookSignatureError


@dataclass
class MockStripeStore:
    sessions: dict[str, dict[str, Any]] = field(default_factory=dict)
    events: dict[str, dict[str, Any]] = field(default_factory=dict)

    def reset(self) -> None:
        self.sessions.clear()
        self.events.clear()


STORE = MockStripeStore()


@dataclass(frozen=True)
class MockStripeClient:
    store: MockStripeStore = field(default_factory=lambda: STORE)
    provider: str = "mock"

    async def create_checkout_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        session = build_checkout_session(payload)
        self.store.sessions[str(session["id"])] = session
        return session

    async def retrieve_checkout_session(self, session_id: str) -> dict[str, Any]:
        return self.get_session(session_id)

    async def expire_checkout_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if session["status"] != "open":
            raise MockStripeError("Checkout Session is not in an expireable state.")
        session["status"] = "expired"
        session["url"] = None
        return session

    async def complete_checkout_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        return complete_checkout_session_in_store(session, store=self.store)

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.sessions.get(session_id)
        if session is None:
            raise MockStripeError("No such checkout.session.")
        return session

    def webhook_secret(self) -> str:
        return stripe_webhook_secret()

    def sign_webhook_payload(self, payload: str, *, timestamp: int | None = None) -> str:
        return sign_stripe_webhook_payload(payload, self.webhook_secret(), timestamp=timestamp)

    def construct_event(self, payload: str, signature: str) -> dict[str, Any]:
        return construct_stripe_event(payload, signature, self.webhook_secret())


@router.post("/v1/checkout/sessions")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def create_checkout_session(request: Request, response: Response) -> dict[str, Any]:
    del response
    require_mock_routes()
    require_feature_enabled("payments")
    payload = await parse_request_payload(request)
    try:
        return await MockStripeClient().create_checkout_session(payload)
    except MockStripeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/v1/checkout/sessions/{session_id}")
async def retrieve_checkout_session(session_id: str) -> dict[str, Any]:
    require_mock_routes()
    require_feature_enabled("payments")
    try:
        return await MockStripeClient().retrieve_checkout_session(session_id)
    except MockStripeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/v1/checkout/sessions/{session_id}/expire")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def expire_checkout_session(
    request: Request,
    response: Response,
    session_id: str,
) -> dict[str, Any]:
    del request, response
    require_mock_routes()
    require_feature_enabled("payments")
    try:
        return await MockStripeClient().expire_checkout_session(session_id)
    except MockStripeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/dev/stripe/complete")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def complete_mock_checkout(
    request: Request,
    response: Response,
    session_id: str = Query(..., description="Mock Checkout Session id."),
) -> dict[str, Any]:
    del request, response
    require_mock_routes()
    require_feature_enabled("payments")
    try:
        result = await MockStripeClient().complete_checkout_session(session_id)
    except MockStripeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    event_payload = json.dumps(result["event"], separators=(",", ":"), sort_keys=True)
    return {
        **result,
        "webhook_signature": MockStripeClient().sign_webhook_payload(event_payload),
    }


def require_mock_routes() -> None:
    if not dev_routes_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


async def parse_request_payload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            json_payload = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed JSON payload.",
            ) from exc
        if not isinstance(json_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expected JSON object.",
            )
        return cast(dict[str, Any], json_payload)
    form = await request.form()
    payload: dict[str, Any] = {}
    for key, value in form.multi_items():
        assign_form_value(payload, key, coerce_form_value(str(value)))
    return payload


def assign_form_value(payload: dict[str, Any], key: str, value: Any) -> None:
    parts = FORM_KEY_PATTERN.findall(key)
    if not parts:
        return
    current: dict[str, Any] | list[Any] = payload
    for index, part in enumerate(parts):
        is_last = index == len(parts) - 1
        next_is_list = not is_last and parts[index + 1].isdigit()
        if isinstance(current, dict):
            if is_last:
                current[part] = value
                return
            current = current.setdefault(part, [] if next_is_list else {})
        else:
            item_index = int(part)
            while len(current) <= item_index:
                current.append(None)
            if is_last:
                current[item_index] = value
                return
            if current[item_index] is None:
                current[item_index] = [] if next_is_list else {}
            current = current[item_index]


def coerce_form_value(value: str) -> str | int | bool:
    if value in {"true", "false"}:
        return value == "true"
    if value.isdigit():
        return int(value)
    return value


def build_checkout_session(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload.get("mode", "payment")
    if mode not in {"payment", "subscription", "setup"}:
        raise MockStripeError("Checkout Session mode must be payment, subscription, or setup.")
    success_url = payload.get("success_url")
    cancel_url = payload.get("cancel_url")
    if not isinstance(success_url, str) or not success_url:
        raise MockStripeError("Checkout Session requires success_url.")
    if not isinstance(cancel_url, str) or not cancel_url:
        raise MockStripeError("Checkout Session requires cancel_url.")
    amount_total, currency = checkout_amount(payload)
    session_id = f"cs_test_{secrets.token_urlsafe(24)}"
    now = datetime.now(tz=UTC)
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    customer = payload.get("customer") if isinstance(payload.get("customer"), str) else None
    customer_email = (
        payload.get("customer_email") if isinstance(payload.get("customer_email"), str) else None
    )
    return {
        "id": session_id,
        "object": "checkout.session",
        "after_expiration": None,
        "allow_promotion_codes": payload.get("allow_promotion_codes"),
        "amount_subtotal": amount_total,
        "amount_total": amount_total,
        "automatic_tax": {"enabled": False, "liability": None, "status": None},
        "billing_address_collection": payload.get("billing_address_collection"),
        "cancel_url": cancel_url,
        "client_reference_id": payload.get("client_reference_id"),
        "consent": None,
        "consent_collection": None,
        "created": int(now.timestamp()),
        "currency": currency,
        "custom_fields": [],
        "custom_text": {"shipping_address": None, "submit": None},
        "customer": customer,
        "customer_creation": payload.get("customer_creation", "if_required"),
        "customer_details": None,
        "customer_email": customer_email,
        "expires_at": int((now + timedelta(hours=24)).timestamp()),
        "invoice": None,
        "invoice_creation": {
            "enabled": False,
            "invoice_data": {
                "account_tax_ids": None,
                "custom_fields": None,
                "description": None,
                "footer": None,
                "issuer": None,
                "metadata": {},
                "rendering_options": None,
            },
        },
        "livemode": False,
        "locale": payload.get("locale"),
        "metadata": metadata,
        "mode": mode,
        "payment_intent": None,
        "payment_link": None,
        "payment_method_collection": "always",
        "payment_method_options": {},
        "payment_method_types": payload.get("payment_method_types", ["card"]),
        "payment_status": "unpaid",
        "phone_number_collection": {"enabled": False},
        "recovered_from": None,
        "setup_intent": None,
        "shipping_address_collection": None,
        "shipping_cost": None,
        "shipping_details": None,
        "shipping_options": [],
        "status": "open",
        "submit_type": payload.get("submit_type"),
        "subscription": None,
        "success_url": success_url,
        "total_details": {"amount_discount": 0, "amount_shipping": 0, "amount_tax": 0},
        "ui_mode": payload.get("ui_mode", "hosted"),
        "url": f"{MOCK_CHECKOUT_BASE_URL}/{session_id}#mock",
    }


def seed_completed_checkout_session(
    payload: dict[str, Any],
    *,
    seed_key: str,
    store: MockStripeStore = STORE,
) -> dict[str, Any]:
    session = build_checkout_session(payload)
    digest = sha256(f"seed-checkout:{seed_key}".encode()).hexdigest()
    session_id = f"cs_test_seed_{digest[:24]}"
    session["id"] = session_id
    session["created"] = SEED_CHECKOUT_CREATED
    session["expires_at"] = SEED_CHECKOUT_CREATED + 86_400
    session["url"] = f"{MOCK_CHECKOUT_BASE_URL}/{session_id}#mock"
    store.sessions[session_id] = session
    return complete_checkout_session_in_store(session, store=store)


def complete_checkout_session_in_store(
    session: dict[str, Any],
    *,
    store: MockStripeStore,
) -> dict[str, Any]:
    if session["status"] == "expired":
        raise MockStripeError("Expired Checkout Sessions cannot be completed.")
    session["status"] = "complete"
    session["payment_status"] = "paid"
    session["url"] = None
    digest = stable_digest(session)
    session["customer"] = session["customer"] or f"cus_mock_{digest[:24]}"
    if session["mode"] == "subscription":
        session["subscription"] = session["subscription"] or f"sub_mock_{digest[:24]}"
    elif session["mode"] == "payment":
        session["payment_intent"] = session["payment_intent"] or f"pi_mock_{digest[:24]}"
    event = build_checkout_completed_event(session)
    store.events[str(event["id"])] = event
    return {"session": session, "event": event}


def complete_checkout_session_payload(session: dict[str, Any]) -> dict[str, Any]:
    return complete_checkout_session_in_store(session, store=MockStripeStore())


def checkout_amount(payload: dict[str, Any]) -> tuple[int | None, str | None]:
    line_items = payload.get("line_items")
    if not isinstance(line_items, list) or not line_items:
        return None, None
    amount_total = 0
    currency: str | None = None
    for item in line_items:
        if not isinstance(item, dict):
            continue
        quantity = item.get("quantity", 1)
        quantity = quantity if isinstance(quantity, int) and quantity > 0 else 1
        price_data = item.get("price_data")
        if isinstance(price_data, dict):
            unit_amount = price_data.get("unit_amount", 0)
            if isinstance(unit_amount, int):
                amount_total += unit_amount * quantity
            if isinstance(price_data.get("currency"), str):
                currency = price_data["currency"]
    return amount_total, currency


def build_checkout_completed_event(session: dict[str, Any]) -> dict[str, Any]:
    digest = stable_digest(session)
    created = int(datetime.now(tz=UTC).timestamp())
    return {
        "id": f"evt_mock_{digest[:24]}",
        "object": "event",
        "api_version": "2025-06-30.basil",
        "created": created,
        "data": {"object": session},
        "livemode": False,
        "pending_webhooks": 1,
        "request": {"id": None, "idempotency_key": None},
        "type": "checkout.session.completed",
    }


def stable_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(encoded).hexdigest()
