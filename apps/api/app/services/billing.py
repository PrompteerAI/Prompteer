"""Billing side effects that must be shared by API routes and webhooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlmodel import Session, select

from app.models.domain import User, utc_now


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
    if event_type != "checkout.session.completed":
        return StripeWebhookResult(event_id=event_id, event_type=event_type, processed=False)

    data = event.get("data")
    checkout_session = data.get("object") if isinstance(data, dict) else None
    if not isinstance(checkout_session, dict):
        return StripeWebhookResult(event_id=event_id, event_type=event_type, processed=False)

    return mark_customer_paid(
        db_session, event_id=event_id, event_type=event_type, checkout_session=checkout_session
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
    db_session.commit()
    return StripeWebhookResult(
        event_id=event_id,
        event_type=event_type,
        processed=True,
        customer_email=normalized_customer_email,
        user_id=user.id,
    )
