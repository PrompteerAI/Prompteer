from app.core.config import settings
from app.integrations.payments.base import PaymentsClient
from app.integrations.payments.mock import MockStripeClient
from app.integrations.payments.real import StripeClient


def get_payments_client() -> PaymentsClient:
    if settings.stripe_secret_key:
        return StripeClient(api_key=settings.stripe_secret_key)
    return MockStripeClient()
