"""Billing side effects that must be shared by API routes and webhooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlmodel import Session

from app.integrations.payments.webhooks import construct_stripe_event
from app.models.domain import StripeCheckoutSession, User
from app.repositories import billing as billing_repository
from app.repositories import users as users_repository


@dataclass(frozen=True)
class StripeWebhookResult:
    event_id: str
    event_type: str
    processed: bool
    customer_email: str | None = None
    user_id: str | None = None


def normalized_email(email: str) -> str:
    return billing_repository.normalized_email(email)


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
