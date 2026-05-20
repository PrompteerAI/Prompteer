from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Request, Response, status

from app.api.deps import get_optional_principal
from app.core.config import settings
from app.core.feature_flags import dev_routes_enabled, require_feature_enabled
from app.core.ratelimit import PAYMENTS_RATE_LIMIT, limiter
from app.core.security import Principal
from app.integrations.payments import get_payments_client
from app.integrations.payments.mock import MockStripeClient, MockStripeError
from app.schemas.billing import CheckoutCreateRequest, CheckoutSessionRead

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
) -> CheckoutSessionRead:
    del request, response, principal
    require_feature_enabled("payments")
    if not dev_routes_enabled() or settings.stripe_secret_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    try:
        result = await MockStripeClient().complete_checkout_session(session_id)
    except MockStripeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return checkout_session_to_read(result["session"], provider="mock")


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
