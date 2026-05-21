"""Email client factory selecting SendGrid real mode or local mock capture."""

from app.core.config import credential_value, settings
from app.integrations.email.base import EmailClient
from app.integrations.email.mock import MockSendGridClient
from app.integrations.email.real import SendGridClient


def get_email_client() -> EmailClient:
    sendgrid_api_key = credential_value(settings.sendgrid_api_key)
    if sendgrid_api_key:
        return SendGridClient(api_key=sendgrid_api_key)
    return MockSendGridClient()
