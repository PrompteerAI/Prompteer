"""Payment client factory selecting Stripe real mode or local mock checkout."""

from app.core.config import credential_value, settings
from app.integrations.payments.base import PaymentsClient
from app.integrations.payments.mock import MockStripeClient
from app.integrations.payments.real import StripeClient


def get_payments_client() -> PaymentsClient:
    stripe_secret_key = credential_value(settings.stripe_secret_key)
    if stripe_secret_key:
        return StripeClient(api_key=stripe_secret_key)
    return MockStripeClient()
