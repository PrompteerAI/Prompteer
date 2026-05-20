"""Tests for SendGrid mock capture, mailbox routes, and real client payloads."""

import asyncio
import json
from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.ratelimit import EMAIL_RATE_LIMIT, limiter
from app.integrations.email import get_email_client
from app.integrations.email import mock as email_mock
from app.integrations.email.mock import MockSendGridClient
from app.integrations.email.real import SendGridClient
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    limiter.reset()


@pytest.mark.asyncio
async def test_mock_sendgrid_captures_eml(tmp_path: Path) -> None:
    client = MockSendGridClient(mailbox_dir=tmp_path)

    result = await client.send(
        {
            "personalizations": [{"to": [{"email": "free@prompteer.dev"}]}],
            "from": {"email": "no-reply@prompteer.dev"},
            "subject": "Welcome to Prompteer",
            "content": [{"type": "text/plain", "value": "Hello from the mock mailbox."}],
        }
    )

    messages = client.list_messages()
    assert result == {"status": "accepted", "captured": "1"}
    assert len(messages) == 1
    assert messages[0]["to"] == "free@prompteer.dev"
    message_path = Path(messages[0]["path"])
    message_text = await asyncio.to_thread(message_path.read_text, encoding="utf-8")
    assert message_text.count("Welcome to Prompteer") == 1


def test_mock_sendgrid_http_route_and_mailbox_detail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(email_mock, "default_mailbox_dir", lambda: tmp_path / ".mock" / "email")
    client = TestClient(create_app())

    send_response = client.post(
        "/v3/mail/send",
        json={
            "personalizations": [{"to": [{"email": "paid@prompteer.dev"}]}],
            "from": {"email": "no-reply@prompteer.dev"},
            "subject": "Receipt",
            "content": [{"type": "text/plain", "value": "Thanks for subscribing."}],
        },
    )
    assert send_response.status_code == 202
    assert send_response.text == ""

    mailbox_response = client.get("/api/v1/dev/mailbox")
    assert mailbox_response.status_code == 200
    message_id = mailbox_response.json()["messages"][0]["id"]

    detail_response = client.get(f"/api/v1/dev/mailbox/{message_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["subject"] == "Receipt"
    assert "Thanks for subscribing." in detail["raw"]


def test_mock_sendgrid_http_route_rejects_invalid_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(email_mock, "default_mailbox_dir", lambda: tmp_path / ".mock" / "email")
    client = TestClient(create_app())

    response = client.post(
        "/v3/mail/send",
        json={
            "personalizations": [{"to": [{"email": "not-an-email"}]}],
            "from": {"email": "no-reply@prompteer.dev"},
            "subject": "Invalid",
            "content": [{"type": "application/json", "value": "{}"}],
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert "errors" in body
    assert {error["field"] for error in body["errors"]} == {
        "personalizations.0.to.0.email",
        "content.0.type",
    }


def test_mock_sendgrid_http_route_is_rate_limited(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(email_mock, "default_mailbox_dir", lambda: tmp_path / ".mock" / "email")
    client = TestClient(create_app())
    payload = {
        "personalizations": [{"to": [{"email": "paid@prompteer.dev"}]}],
        "from": {"email": "no-reply@prompteer.dev"},
        "subject": "Rate limit check",
        "content": [{"type": "text/plain", "value": "Hello"}],
    }

    allowed_requests = int(EMAIL_RATE_LIMIT.split("/", 1)[0])
    for _ in range(allowed_requests):
        assert client.post("/v3/mail/send", json=payload).status_code == 202

    response = client.post("/v3/mail/send", json=payload)

    assert response.status_code == 429
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "rate_limited"


def test_email_factory_selects_real_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "sendgrid_api_key", "SG.test")
    assert isinstance(get_email_client(), SendGridClient)

    monkeypatch.setattr(settings, "sendgrid_api_key", "")
    assert isinstance(get_email_client(), MockSendGridClient)


@pytest.mark.asyncio
async def test_sendgrid_real_client_posts_mail_send_payload() -> None:
    payload = {
        "personalizations": [{"to": [{"email": "paid@prompteer.dev"}]}],
        "from": {"email": "no-reply@prompteer.dev"},
        "subject": "Receipt",
        "content": [{"type": "text/plain", "value": "Thanks for subscribing."}],
    }
    with respx.mock:
        route = respx.post("https://sendgrid.example/v3/mail/send").mock(
            return_value=httpx.Response(202)
        )
        client = SendGridClient(api_key="SG.test", base_url="https://sendgrid.example")

        result = await client.send(payload)

    assert result == {"status": "accepted", "captured": "0"}
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer SG.test"
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == payload
