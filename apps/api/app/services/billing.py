"""Billing side effects that must be shared by API routes and webhooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.domain import StripeWebhookEvent, User, utc_now


@dataclass(frozen=True)
class StripeWebhookResult:
    event_id: str
    event_type: str
    processed: bool
    customer_email: str | None = None
    user_id: str | None = None


def apply_stripe_webhook_event(db_session: Session, event: dict[str, Any]) -> StripeWebhookResult:
    event_id = str(event.get("id", ""))
    event_type = str(event.get("type", ""))
    existing_event = db_session.get(StripeWebhookEvent, event_id)
    if existing_event is not None:
        return webhook_event_to_result(existing_event, duplicate=True)

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


def record_stripe_webhook_event(
    db_session: Session,
    result: StripeWebhookResult,
) -> StripeWebhookResult:
    db_session.add(
        StripeWebhookEvent(
            event_id=result.event_id,
            event_type=result.event_type,
            processed=result.processed,
            customer_email=result.customer_email,
            user_id=result.user_id,
        )
    )
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        existing_event = db_session.get(StripeWebhookEvent, result.event_id)
        if existing_event is not None:
            return webhook_event_to_result(existing_event, duplicate=True)
        raise
    return result


def webhook_event_to_result(
    event: StripeWebhookEvent,
    *,
    duplicate: bool,
) -> StripeWebhookResult:
    return StripeWebhookResult(
        event_id=event.event_id,
        event_type=event.event_type,
        processed=False if duplicate else event.processed,
        customer_email=event.customer_email,
        user_id=event.user_id,
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

    user = db_session.exec(select(User).where(User.email == normalized_customer_email)).first()
    if user is None:
        return StripeWebhookResult(
            event_id=event_id,
            event_type=event_type,
            processed=False,
            customer_email=normalized_customer_email,
        )

    user.plan = "paid"
    user.updated_at = utc_now()
    db_session.add(user)
    return StripeWebhookResult(
        event_id=event_id,
        event_type=event_type,
        processed=True,
        customer_email=normalized_customer_email,
        user_id=user.id,
    )
