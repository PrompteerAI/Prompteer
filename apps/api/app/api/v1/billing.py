"""API v1 billing routes; no sibling billing API version exists yet."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, Response, status
from sqlmodel import Session

from app.api.deps import get_current_principal
from app.core.feature_flags import require_feature_enabled
from app.core.ratelimit import (
    GENERAL_RATE_LIMIT,
    PAYMENTS_RATE_LIMIT,
    STRIPE_WEBHOOK_RATE_LIMIT,
    limiter,
)
from app.core.security import Principal
from app.db.session import get_session
from app.integrations.payments.webhooks import StripeWebhookSignatureError
from app.schemas.billing import (
    BillingSubscriptionRead,
    CheckoutCreateRequest,
    CheckoutSessionRead,
    StripeWebhookRead,
)
from app.services.billing import (
    BillingSubscription,
    CheckoutSessionInvalidError,
    CheckoutSessionNotFoundError,
    CheckoutSessionResult,
    MockCheckoutUnavailableError,
    StripeWebhookResult,
    complete_mock_checkout_for_user,
    create_checkout_session_for_user,
    get_billing_subscription,
    process_signed_stripe_webhook_payload,
    retrieve_checkout_session_for_user,
)
from app.services.llm_quota import resolve_user_for_principal

router = APIRouter(prefix="/billing", tags=["billing"])


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
    return billing_subscription_to_read(get_billing_subscription(user))


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
    result = await create_checkout_session_for_user(
        db_session,
        user=user,
        plan=checkout_request.plan,
    )
    return checkout_session_result_to_read(result)


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
    try:
        result = await retrieve_checkout_session_for_user(
            db_session,
            user=user,
            session_id=session_id,
        )
    except CheckoutSessionNotFoundError as exc:
        raise checkout_session_not_found(exc) from exc
    return checkout_session_result_to_read(result)


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
    try:
        result = await complete_mock_checkout_for_user(
            db_session,
            user=user,
            session_id=session_id,
        )
    except (CheckoutSessionNotFoundError, MockCheckoutUnavailableError) as exc:
        raise checkout_session_not_found(exc) from exc
    except CheckoutSessionInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return checkout_session_result_to_read(result)


@router.post("/webhooks/stripe")
@limiter.limit(STRIPE_WEBHOOK_RATE_LIMIT)
async def stripe_webhook(
    request: Request,
    response: Response,
    db_session: Annotated[Session, Depends(get_session)],
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> StripeWebhookRead:
    del response
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
    try:
        result = await process_signed_stripe_webhook_payload(
            db_session,
            payload,
            stripe_signature,
        )
    except StripeWebhookSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return stripe_webhook_to_read(result)


def checkout_session_not_found(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def checkout_session_result_to_read(result: CheckoutSessionResult) -> CheckoutSessionRead:
    return checkout_session_to_read(result.session, provider=result.provider)


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


def billing_subscription_to_read(subscription: BillingSubscription) -> BillingSubscriptionRead:
    return BillingSubscriptionRead(
        plan=subscription.plan,
        status=subscription.status,
        customer_email=subscription.customer_email,
        provider=subscription.provider,
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
