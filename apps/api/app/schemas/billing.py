"""Pydantic response and request schemas for billing checkout routes."""

from typing import Literal

from pydantic import BaseModel, EmailStr


class CheckoutCreateRequest(BaseModel):
    plan: Literal["pro_monthly"] = "pro_monthly"
    customer_email: EmailStr = "paid@prompteer.dev"


class CheckoutSessionRead(BaseModel):
    id: str
    mode: str
    status: str
    payment_status: str
    amount_total: int | None
    currency: str | None
    url: str | None
    customer_email: str | None
    provider: str


class BillingSubscriptionRead(BaseModel):
    plan: str
    status: Literal["active", "inactive"]
    customer_email: EmailStr
    provider: str


class StripeWebhookRead(BaseModel):
    received: bool
    event_id: str
    event_type: str
    processed: bool
    customer_email: str | None
    user_id: str | None
