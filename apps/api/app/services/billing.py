"""Billing workflows shared by API routes, dev routes, and webhooks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import structlog
from sqlmodel import Session

from app.core.config import integration_modes, settings
from app.core.feature_flags import dev_routes_enabled, feature_enabled
from app.integrations.email import get_email_client
from app.integrations.payments.webhooks import construct_stripe_event
from app.models.domain import StripeCheckoutSession, User
from app.repositories import billing as billing_repository
from app.repositories import users as users_repository

logger = structlog.get_logger(__name__)
PRO_MONTHLY_PRICE_CENTS = 1200


class BillingServiceError(Exception):
    """Base class for expected billing workflow failures."""


class CheckoutSessionNotFoundError(BillingServiceError):
    """Raised when a checkout session does not exist or does not belong to the user."""

    def __init__(self) -> None:
        super().__init__("No such checkout.session.")


class MockCheckoutUnavailableError(BillingServiceError):
    """Raised when the dev-only mock checkout completion flow is disabled."""

    def __init__(self) -> None:
        super().__init__("Not found")


class CheckoutSessionInvalidError(BillingServiceError):
    """Raised when a checkout session cannot transition to the requested state."""


@dataclass(frozen=True)
class StripeWebhookResult:
    event_id: str
    event_type: str
    processed: bool
    customer_email: str | None = None
    user_id: str | None = None


@dataclass(frozen=True)
class CheckoutSessionResult:
    session: dict[str, Any]
    provider: str


@dataclass(frozen=True)
class BillingSubscription:
    plan: str
    status: str
    customer_email: str
    provider: str


def normalized_email(email: str) -> str:
    return billing_repository.normalized_email(email)


def get_billing_subscription(user: User) -> BillingSubscription:
    return BillingSubscription(
        plan=user.plan,
        status="active" if user.plan == "paid" else "inactive",
        customer_email=user.email,
        provider="stripe" if integration_modes()["stripe"] == "real" else "mock",
    )


async def create_checkout_session_for_user(
    db_session: Session,
    *,
    user: User,
    plan: str,
) -> CheckoutSessionResult:
    from app.integrations.payments import get_payments_client

    client = get_payments_client()
    checkout_session = await client.create_checkout_session(checkout_payload(plan, user=user))
    record_checkout_session(
        db_session,
        checkout_session,
        user=user,
        provider=client.provider,
        plan=plan,
    )
    return CheckoutSessionResult(session=checkout_session, provider=client.provider)


async def retrieve_checkout_session_for_user(
    db_session: Session,
    *,
    user: User,
    session_id: str,
) -> CheckoutSessionResult:
    from app.integrations.payments import get_payments_client

    client = get_payments_client()
    if client.provider == "mock":
        checkout_session = require_recorded_checkout_session(db_session, session_id)
    else:
        checkout_session = await client.retrieve_checkout_session(session_id)
    require_checkout_owner(checkout_session, user)
    return CheckoutSessionResult(session=checkout_session, provider=client.provider)


async def complete_mock_checkout_for_user(
    db_session: Session,
    *,
    user: User,
    session_id: str,
) -> CheckoutSessionResult:
    if not dev_routes_enabled() or integration_modes()["stripe"] != "mock":
        raise MockCheckoutUnavailableError()

    from app.integrations.payments.mock import MockStripeError

    try:
        checkout_session = require_recorded_checkout_session(db_session, session_id)
        require_checkout_owner(checkout_session, user)
        result = complete_checkout_session_payload(checkout_session)
    except CheckoutSessionNotFoundError:
        raise
    except MockStripeError as exc:
        raise CheckoutSessionInvalidError(str(exc)) from exc

    update_checkout_session_record(db_session, result["session"])
    completed_checkout_session = result["session"]
    webhook_result = process_mock_checkout_webhook(db_session, result["event"])
    await send_checkout_receipt_email(completed_checkout_session, webhook_result=webhook_result)
    return CheckoutSessionResult(session=completed_checkout_session, provider="mock")


def apply_stripe_webhook_event(db_session: Session, event: dict[str, Any]) -> StripeWebhookResult:
    event_id = str(event.get("id", ""))
    event_type = str(event.get("type", ""))
    existing_event = billing_repository.get_stripe_webhook_event(db_session, event_id)
    if existing_event is not None:
        return stripe_webhook_result_from_stored(
            billing_repository.webhook_event_to_result(existing_event, duplicate=True)
        )

    if event_type != "checkout.session.completed":
        result = StripeWebhookResult(event_id=event_id, event_type=event_type, processed=False)
        return record_stripe_webhook_event(db_session, result)

    data = event.get("data")
    checkout_session = data.get("object") if isinstance(data, dict) else None
    if not isinstance(checkout_session, dict):
        result = StripeWebhookResult(event_id=event_id, event_type=event_type, processed=False)
        return record_stripe_webhook_event(db_session, result)

    result = mark_customer_paid(
        db_session, event_id=event_id, event_type=event_type, checkout_session=checkout_session
    )
    return record_stripe_webhook_event(db_session, result)


def apply_signed_stripe_webhook_payload(
    db_session: Session,
    payload: str,
    stripe_signature: str,
) -> StripeWebhookResult:
    event = construct_stripe_event(payload, stripe_signature)
    return apply_stripe_webhook_event(db_session, event)


async def process_signed_stripe_webhook_payload(
    db_session: Session,
    payload: str,
    stripe_signature: str,
) -> StripeWebhookResult:
    event = construct_stripe_event(payload, stripe_signature)
    result = apply_stripe_webhook_event(db_session, event)
    checkout_session = checkout_session_from_stripe_event(event)
    if checkout_session is not None:
        await send_checkout_receipt_email(checkout_session, webhook_result=result)
    return result


def process_mock_checkout_webhook(
    db_session: Session,
    event: dict[str, object],
) -> StripeWebhookResult:
    from app.integrations.payments.mock import MockStripeClient

    payload = stripe_event_payload(event)
    signature = MockStripeClient().sign_webhook_payload(payload)
    return apply_signed_stripe_webhook_payload(db_session, payload, signature)


def record_stripe_webhook_event(
    db_session: Session,
    result: StripeWebhookResult,
) -> StripeWebhookResult:
    stored = billing_repository.record_stripe_webhook_event(
        db_session,
        billing_repository.StoredWebhookResult(
            event_id=result.event_id,
            event_type=result.event_type,
            processed=result.processed,
            customer_email=result.customer_email,
            user_id=result.user_id,
        ),
    )
    return stripe_webhook_result_from_stored(stored)


def stripe_webhook_result_from_stored(
    stored: billing_repository.StoredWebhookResult,
) -> StripeWebhookResult:
    return StripeWebhookResult(
        event_id=stored.event_id,
        event_type=stored.event_type,
        processed=stored.processed,
        customer_email=stored.customer_email,
        user_id=stored.user_id,
    )


def mark_customer_paid(
    db_session: Session,
    *,
    event_id: str,
    event_type: str,
    checkout_session: dict[str, Any],
) -> StripeWebhookResult:
    customer_email = checkout_session.get("customer_email")
    if not isinstance(customer_email, str):
        return StripeWebhookResult(event_id=event_id, event_type=event_type, processed=False)

    normalized_customer_email = customer_email.strip().lower()
    if not normalized_customer_email:
        return StripeWebhookResult(event_id=event_id, event_type=event_type, processed=False)

    user = users_repository.get_user_by_email(db_session, normalized_customer_email)
    if user is None:
        return StripeWebhookResult(
            event_id=event_id,
            event_type=event_type,
            processed=False,
            customer_email=normalized_customer_email,
        )
    if not checkout_session_matches_user(checkout_session, user):
        return StripeWebhookResult(
            event_id=event_id,
            event_type=event_type,
            processed=False,
            customer_email=normalized_customer_email,
            user_id=user.id,
        )

    if not checkout_session_matches_local_record(db_session, checkout_session, user):
        return StripeWebhookResult(
            event_id=event_id,
            event_type=event_type,
            processed=False,
            customer_email=normalized_customer_email,
            user_id=user.id,
        )

    users_repository.mark_user_paid(db_session, user)
    update_checkout_session_record(db_session, checkout_session, commit=False)
    return StripeWebhookResult(
        event_id=event_id,
        event_type=event_type,
        processed=True,
        customer_email=normalized_customer_email,
        user_id=user.id,
    )


def checkout_session_matches_user(checkout_session: dict[str, Any], user: User) -> bool:
    client_reference_id = checkout_session.get("client_reference_id")
    if (
        isinstance(client_reference_id, str)
        and client_reference_id
        and client_reference_id != user.id
    ):
        return False
    if isinstance(client_reference_id, str) and client_reference_id == user.id:
        return True

    metadata = checkout_session.get("metadata")
    if isinstance(metadata, dict):
        metadata_user_id = metadata.get("user_id")
        if isinstance(metadata_user_id, str) and metadata_user_id and metadata_user_id != user.id:
            return False
        if isinstance(metadata_user_id, str) and metadata_user_id == user.id:
            return True
    return False


def require_checkout_owner(checkout_session: dict[str, Any], user: User) -> None:
    customer_email = checkout_session.get("customer_email")
    if isinstance(customer_email, str) and normalized_email(customer_email) == user.email:
        return
    client_reference_id = checkout_session.get("client_reference_id")
    if isinstance(client_reference_id, str) and client_reference_id == user.id:
        return
    raise CheckoutSessionNotFoundError()


def require_recorded_checkout_session(db_session: Session, session_id: str) -> dict[str, Any]:
    checkout_session = get_recorded_checkout_session_payload(db_session, session_id)
    if checkout_session is None:
        raise CheckoutSessionNotFoundError()
    return checkout_session


def checkout_payload(plan: str, *, user: User) -> dict[str, Any]:
    return {
        "mode": "subscription",
        "success_url": f"{settings.app_url}/en/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.app_url}/en/billing",
        "customer_email": user.email,
        "client_reference_id": user.id,
        "metadata": {"plan": plan, "user_id": user.id},
        "line_items": [
            {
                "quantity": 1,
                "price_data": {
                    "currency": "usd",
                    "unit_amount": PRO_MONTHLY_PRICE_CENTS,
                    "recurring": {"interval": "month"},
                    "product_data": {"name": "Prompteer Pro"},
                },
            }
        ],
    }


async def send_checkout_receipt_email(
    checkout_session: dict[str, Any],
    *,
    webhook_result: StripeWebhookResult,
) -> None:
    if (
        not webhook_result.processed
        or not webhook_result.customer_email
        or not feature_enabled("email")
    ):
        return
    try:
        await get_email_client().send(
            checkout_receipt_payload(
                checkout_session,
                customer_email=webhook_result.customer_email,
                event_id=webhook_result.event_id,
                event_type=webhook_result.event_type,
            )
        )
    except Exception as exc:
        logger.warning(
            "checkout_receipt_email_failed",
            event_id=webhook_result.event_id,
            checkout_session_id=checkout_session.get("id"),
            exc_info=exc,
        )


def checkout_receipt_payload(
    checkout_session: dict[str, Any],
    *,
    customer_email: str,
    event_id: str,
    event_type: str,
) -> dict[str, Any]:
    amount = checkout_session.get("amount_total")
    currency = checkout_session.get("currency")
    amount_text = format_checkout_amount(amount, currency)
    session_id = str(checkout_session.get("id", "unknown"))
    return {
        "personalizations": [{"to": [{"email": customer_email}]}],
        "from": {"email": settings.sendgrid_from_email},
        "subject": "Prompteer Pro receipt",
        "content": [
            {
                "type": "text/plain",
                "value": (
                    "Your Prompteer Pro checkout is complete.\n\n"
                    f"Checkout session: {session_id}\n"
                    f"Stripe event: {event_id}\n"
                    f"Event type: {event_type}\n"
                    f"Amount: {amount_text}\n"
                    f"Status: {checkout_session.get('status')}\n"
                    f"Payment status: {checkout_session.get('payment_status')}\n"
                ),
            }
        ],
    }


def format_checkout_amount(amount: Any, currency: Any) -> str:
    if isinstance(amount, int) and isinstance(currency, str) and currency:
        return f"{amount / 100:.2f} {currency.upper()}"
    return "unknown"


def checkout_session_from_stripe_event(event: dict[str, Any]) -> dict[str, Any] | None:
    data = event.get("data")
    checkout_session = data.get("object") if isinstance(data, dict) else None
    return checkout_session if isinstance(checkout_session, dict) else None


def stripe_event_payload(event: dict[str, object]) -> str:
    return json.dumps(event, separators=(",", ":"), sort_keys=True)


def complete_checkout_session_payload(session: dict[str, Any]) -> dict[str, Any]:
    from app.integrations.payments.mock import complete_checkout_session_payload as complete

    return complete(session)


def record_checkout_session(
    db_session: Session,
    checkout_session: dict[str, Any],
    *,
    user: User,
    provider: str,
    plan: str,
) -> StripeCheckoutSession:
    return billing_repository.record_checkout_session(
        db_session,
        checkout_session,
        user=user,
        provider=provider,
        plan=plan,
    )


def get_recorded_checkout_session_payload(
    db_session: Session,
    session_id: str,
) -> dict[str, Any] | None:
    return billing_repository.get_recorded_checkout_session_payload(db_session, session_id)


def update_checkout_session_record(
    db_session: Session,
    checkout_session: dict[str, Any],
    *,
    commit: bool = True,
) -> StripeCheckoutSession | None:
    return billing_repository.update_checkout_session_record(
        db_session,
        checkout_session,
        commit=commit,
    )


def checkout_session_matches_local_record(
    db_session: Session,
    checkout_session: dict[str, Any],
    user: User,
) -> bool:
    return billing_repository.checkout_session_matches_local_record(
        db_session,
        checkout_session,
        user,
    )
