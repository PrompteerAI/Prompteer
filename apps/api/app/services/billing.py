"""Billing side effects that must be shared by API routes and webhooks."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.integrations.payments.webhooks import construct_stripe_event
from app.models.domain import StripeCheckoutSession, StripeWebhookEvent, User, utc_now


@dataclass(frozen=True)
class StripeWebhookResult:
    event_id: str
    event_type: str
    processed: bool
    customer_email: str | None = None
    user_id: str | None = None


def normalized_email(email: str) -> str:
    return email.strip().lower()


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


def apply_signed_stripe_webhook_payload(
    db_session: Session,
    payload: str,
    stripe_signature: str,
) -> StripeWebhookResult:
    event = construct_stripe_event(payload, stripe_signature)
    return apply_stripe_webhook_event(db_session, event)


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

    user.plan = "paid"
    user.updated_at = utc_now()
    db_session.add(user)
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


def record_checkout_session(
    db_session: Session,
    checkout_session: dict[str, Any],
    *,
    user: User,
    provider: str,
    plan: str,
) -> StripeCheckoutSession:
    row = db_session.get(StripeCheckoutSession, str(checkout_session["id"]))
    if row is None:
        row = StripeCheckoutSession(
            provider_session_id=str(checkout_session["id"]),
            user_id=user.id,
            mode=str(checkout_session.get("mode", "")),
            status=str(checkout_session.get("status", "")),
            payment_status=str(checkout_session.get("payment_status", "")),
        )
    apply_checkout_session_payload(
        row,
        checkout_session,
        user=user,
        provider=provider,
        plan=plan,
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


def get_recorded_checkout_session_payload(
    db_session: Session,
    session_id: str,
) -> dict[str, Any] | None:
    row = db_session.get(StripeCheckoutSession, session_id)
    if row is None:
        return None
    return deepcopy(row.checkout_payload)


def update_checkout_session_record(
    db_session: Session,
    checkout_session: dict[str, Any],
    *,
    commit: bool = True,
) -> StripeCheckoutSession | None:
    row = db_session.get(StripeCheckoutSession, str(checkout_session.get("id", "")))
    if row is None:
        return None
    apply_checkout_session_payload(
        row,
        checkout_session,
        user_id=row.user_id,
        provider=row.provider,
        plan=row.plan,
    )
    db_session.add(row)
    if commit:
        db_session.commit()
        db_session.refresh(row)
    return row


def apply_checkout_session_payload(
    row: StripeCheckoutSession,
    checkout_session: dict[str, Any],
    *,
    user: User | None = None,
    user_id: str | None = None,
    provider: str,
    plan: str,
) -> None:
    row.provider = provider
    row.user_id = user.id if user is not None else str(user_id)
    row.plan = plan
    row.mode = str(checkout_session.get("mode", ""))
    row.status = str(checkout_session.get("status", ""))
    row.payment_status = str(checkout_session.get("payment_status", ""))
    amount_total = checkout_session.get("amount_total")
    row.amount_total = amount_total if isinstance(amount_total, int) else None
    currency = checkout_session.get("currency")
    row.currency = currency if isinstance(currency, str) else None
    customer_email = checkout_session.get("customer_email")
    row.customer_email = (
        normalized_email(customer_email) if isinstance(customer_email, str) else None
    )
    client_reference_id = checkout_session.get("client_reference_id")
    row.client_reference_id = client_reference_id if isinstance(client_reference_id, str) else None
    metadata = checkout_session.get("metadata")
    row.session_metadata = deepcopy(metadata) if isinstance(metadata, dict) else {}
    row.checkout_payload = deepcopy(checkout_session)
    row.updated_at = utc_now()


def checkout_session_matches_local_record(
    db_session: Session,
    checkout_session: dict[str, Any],
    user: User,
) -> bool:
    session_id = checkout_session.get("id")
    if not isinstance(session_id, str) or not session_id:
        return False
    row = db_session.get(StripeCheckoutSession, session_id)
    if row is None or row.user_id != user.id:
        return False
    if row.status == "expired":
        return False
    if row.mode != checkout_session.get("mode"):
        return False
    if row.amount_total != checkout_session.get("amount_total"):
        return False
    if row.currency != checkout_session.get("currency"):
        return False
    return not (
        row.client_reference_id
        and row.client_reference_id != checkout_session.get("client_reference_id")
    )
