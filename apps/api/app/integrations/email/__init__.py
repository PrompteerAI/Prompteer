from app.core.config import settings
from app.integrations.email.base import EmailClient
from app.integrations.email.mock import MockSendGridClient
from app.integrations.email.real import SendGridClient


def get_email_client() -> EmailClient:
    if settings.sendgrid_api_key:
        return SendGridClient(api_key=settings.sendgrid_api_key)
    return MockSendGridClient()
