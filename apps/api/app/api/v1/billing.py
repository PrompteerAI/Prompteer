"""API v1 billing routes; no sibling billing API version exists yet."""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response, status
from sqlmodel import Session

from app.api.deps import get_optional_principal
from app.core.config import settings
from app.core.feature_flags import dev_routes_enabled, require_feature_enabled
from app.core.ratelimit import PAYMENTS_RATE_LIMIT, limiter
from app.core.security import Principal
from app.db.session import get_session
from app.integrations.payments import get_payments_client
from app.integrations.payments.mock import MockStripeClient, MockStripeError
from app.integrations.payments.webhooks import StripeWebhookSignatureError, construct_stripe_event
from app.schemas.billing import CheckoutCreateRequest, CheckoutSessionRead, StripeWebhookRead
from app.services.billing import StripeWebhookResult, apply_stripe_webhook_event

router = APIRouter(prefix="/billing", tags=["billing"])

PRO_MONTHLY_PRICE_CENTS = 1200


@router.post("/checkout")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def create_checkout(
    request: Request,
    response: Response,
    checkout_request: CheckoutCreateRequest,
    principal: Annotated[Principal | None, Depends(get_optional_principal)],
) -> CheckoutSessionRead:
    del request, response, principal
    require_feature_enabled("payments")
    client = get_payments_client()
    session = await client.create_checkout_session(checkout_payload(checkout_request))
    return checkout_session_to_read(session, provider=client.provider)


@router.get("/checkout/{session_id}")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def retrieve_checkout(
    request: Request,
    response: Response,
    session_id: Annotated[str, Path(min_length=8)],
    principal: Annotated[Principal | None, Depends(get_optional_principal)],
) -> CheckoutSessionRead:
    del request, response, principal
    require_feature_enabled("payments")
    client = get_payments_client()
    try:
        session = await client.retrieve_checkout_session(session_id)
    except MockStripeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return checkout_session_to_read(session, provider=client.provider)


@router.post("/checkout/{session_id}/complete")
@limiter.limit(PAYMENTS_RATE_LIMIT)
async def complete_mock_checkout(
    request: Request,
    response: Response,
    session_id: Annotated[str, Path(min_length=8)],
    principal: Annotated[Principal | None, Depends(get_optional_principal)],
    db_session: Annotated[Session, Depends(get_session)],
) -> CheckoutSessionRead:
    del request, response, principal
    require_feature_enabled("payments")
    if not dev_routes_enabled() or settings.stripe_secret_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        result = await MockStripeClient().complete_checkout_session(session_id)
    except MockStripeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    checkout_session = result["session"]
    process_mock_checkout_webhook(db_session, result["event"])
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
    result = handle_stripe_webhook_payload(db_session, payload, stripe_signature)
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
        event = construct_stripe_event(payload, stripe_signature)
    except StripeWebhookSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return apply_stripe_webhook_event(db_session, event)


def stripe_event_payload(event: dict[str, object]) -> str:
    return json.dumps(event, separators=(",", ":"), sort_keys=True)


def checkout_payload(request: CheckoutCreateRequest) -> dict[str, Any]:
    return {
        "mode": "subscription",
        "success_url": f"{settings.app_url}/en/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.app_url}/en/billing",
        "customer_email": request.customer_email,
        "metadata": {"plan": request.plan},
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


def stripe_webhook_to_read(result: StripeWebhookResult) -> StripeWebhookRead:
    return StripeWebhookRead(
        received=True,
        event_id=result.event_id,
        event_type=result.event_type,
        processed=result.processed,
        customer_email=result.customer_email,
        user_id=result.user_id,
    )
