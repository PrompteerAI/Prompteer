"""API v1 billing routes; no sibling billing API version exists yet."""

import json
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response, status
from sqlmodel import Session

from app.api.deps import get_current_principal
from app.core.config import settings
from app.core.feature_flags import dev_routes_enabled, feature_enabled, require_feature_enabled
from app.core.ratelimit import GENERAL_RATE_LIMIT, PAYMENTS_RATE_LIMIT, limiter
from app.core.security import Principal
from app.db.session import get_session
from app.integrations.email import get_email_client
from app.integrations.payments import get_payments_client
from app.integrations.payments.mock import (
    MockStripeClient,
    MockStripeError,
    complete_checkout_session_payload,
)
from app.integrations.payments.webhooks import StripeWebhookSignatureError, construct_stripe_event
from app.models.domain import User
from app.schemas.billing import (
    BillingSubscriptionRead,
    CheckoutCreateRequest,
    CheckoutSessionRead,
    StripeWebhookRead,
)
from app.services.billing import (
    StripeWebhookResult,
    apply_signed_stripe_webhook_payload,
    apply_stripe_webhook_event,
    get_recorded_checkout_session_payload,
    record_checkout_session,
    update_checkout_session_record,
)
from app.services.llm_quota import normalized_email, resolve_user_for_principal

router = APIRouter(prefix="/billing", tags=["billing"])
logger = structlog.get_logger(__name__)

PRO_MONTHLY_PRICE_CENTS = 1200


@router.get("/subscription")
@limiter.limit(GENERAL_RATE_LIMIT)
async def read_subscription(
    request: Request,
    response: Response,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db_session: Annotated[Session, Depends(get_session)],
) -> BillingSubscriptionRead:
    del request, response
    require_feature_enabled("payments")
    user = resolve_user_for_principal(db_session, principal)
    return billing_subscription_to_read(user)


@router.post("/checkout")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def create_checkout(
    request: Request,
    response: Response,
    checkout_request: CheckoutCreateRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    db_session: Annotated[Session, Depends(get_session)],
) -> CheckoutSessionRead:
    del request, response
    require_feature_enabled("payments")
    user = resolve_user_for_principal(db_session, principal)
    client = get_payments_client()
    session = await client.create_checkout_session(checkout_payload(checkout_request, user=user))
    record_checkout_session(
        db_session,
        session,
        user=user,
        provider=client.provider,
        plan=checkout_request.plan,
    )
    return checkout_session_to_read(session, provider=client.provider)


@router.get("/checkout/{session_id}")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def retrieve_checkout(
    request: Request,
    response: Response,
    session_id: Annotated[str, Path(min_length=8)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    db_session: Annotated[Session, Depends(get_session)],
) -> CheckoutSessionRead:
    del request, response
    require_feature_enabled("payments")
    user = resolve_user_for_principal(db_session, principal)
    client = get_payments_client()
    if isinstance(client, MockStripeClient):
        session = get_recorded_checkout_or_404(db_session, session_id)
    else:
        try:
            session = await client.retrieve_checkout_session(session_id)
        except MockStripeError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    require_checkout_owner(session, user)
    return checkout_session_to_read(session, provider=client.provider)


@router.post("/checkout/{session_id}/complete")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def complete_mock_checkout(
    request: Request,
    response: Response,
    session_id: Annotated[str, Path(min_length=8)],
    principal: Annotated[Principal, Depends(get_current_principal)],
    db_session: Annotated[Session, Depends(get_session)],
) -> CheckoutSessionRead:
    del request, response
    require_feature_enabled("payments")
    user = resolve_user_for_principal(db_session, principal)
    if not dev_routes_enabled() or settings.stripe_secret_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        session = get_recorded_checkout_or_404(db_session, session_id)
        require_checkout_owner(session, user)
        result = complete_checkout_session_payload(session)
    except MockStripeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    update_checkout_session_record(db_session, result["session"])
    checkout_session = result["session"]
    webhook_result = process_mock_checkout_webhook(db_session, result["event"])
    await send_checkout_receipt_email(checkout_session, webhook_result=webhook_result)
    return checkout_session_to_read(checkout_session, provider="mock")


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    db_session: Annotated[Session, Depends(get_session)],
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> StripeWebhookRead:
    require_feature_enabled("payments")
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header.",
        )
    try:
        payload = (await request.body()).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe webhook payload must be UTF-8 encoded.",
        ) from exc
    event = construct_stripe_webhook_event(payload, stripe_signature)
    result = apply_stripe_webhook_event(db_session, event)
    checkout_session = checkout_session_from_stripe_event(event)
    if checkout_session is not None:
        await send_checkout_receipt_email(checkout_session, webhook_result=result)
    return stripe_webhook_to_read(result)


def process_mock_checkout_webhook(
    db_session: Session,
    event: dict[str, object],
) -> StripeWebhookResult:
    payload = stripe_event_payload(event)
    signature = MockStripeClient().sign_webhook_payload(payload)
    return handle_stripe_webhook_payload(db_session, payload, signature)


def handle_stripe_webhook_payload(
    db_session: Session,
    payload: str,
    stripe_signature: str,
) -> StripeWebhookResult:
    try:
        return apply_signed_stripe_webhook_payload(db_session, payload, stripe_signature)
    except StripeWebhookSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def construct_stripe_webhook_event(payload: str, stripe_signature: str) -> dict[str, Any]:
    try:
        return construct_stripe_event(payload, stripe_signature)
    except StripeWebhookSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def checkout_session_from_stripe_event(event: dict[str, Any]) -> dict[str, Any] | None:
    data = event.get("data")
    checkout_session = data.get("object") if isinstance(data, dict) else None
    return checkout_session if isinstance(checkout_session, dict) else None


def stripe_event_payload(event: dict[str, object]) -> str:
    return json.dumps(event, separators=(",", ":"), sort_keys=True)


def get_recorded_checkout_or_404(db_session: Session, session_id: str) -> dict[str, Any]:
    session = get_recorded_checkout_session_payload(db_session, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such checkout.session."
        )
    return session


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


def checkout_payload(request: CheckoutCreateRequest, *, user: User) -> dict[str, Any]:
    return {
        "mode": "subscription",
        "success_url": f"{settings.app_url}/en/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.app_url}/en/billing",
        "customer_email": user.email,
        "client_reference_id": user.id,
        "metadata": {"plan": request.plan, "user_id": user.id},
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


def require_checkout_owner(session: dict[str, Any], user: User) -> None:
    customer_email = session.get("customer_email")
    if isinstance(customer_email, str) and normalized_email(customer_email) == user.email:
        return
    client_reference_id = session.get("client_reference_id")
    if isinstance(client_reference_id, str) and client_reference_id == user.id:
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such checkout.session.")


def checkout_session_to_read(session: dict[str, Any], *, provider: str) -> CheckoutSessionRead:
    return CheckoutSessionRead(
        id=str(session["id"]),
        mode=str(session["mode"]),
        status=str(session["status"]),
        payment_status=str(session["payment_status"]),
        amount_total=session["amount_total"] if isinstance(session["amount_total"], int) else None,
        currency=session["currency"] if isinstance(session["currency"], str) else None,
        url=session["url"] if isinstance(session["url"], str) else None,
        customer_email=(
            session["customer_email"] if isinstance(session["customer_email"], str) else None
        ),
        provider=provider,
    )


def billing_subscription_to_read(user: User) -> BillingSubscriptionRead:
    return BillingSubscriptionRead(
        plan=user.plan,
        status="active" if user.plan == "paid" else "inactive",
        customer_email=user.email,
        provider="stripe" if settings.stripe_secret_key else "mock",
    )


def stripe_webhook_to_read(result: StripeWebhookResult) -> StripeWebhookRead:
    return StripeWebhookRead(
        received=True,
        event_id=result.event_id,
        event_type=result.event_type,
        processed=result.processed,
        customer_email=result.customer_email,
        user_id=result.user_id,
    )
