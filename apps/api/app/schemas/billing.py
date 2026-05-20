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
