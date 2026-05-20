from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.integrations.email import mock as email_mock
from app.integrations.email.mock import MockSendGridClient
from app.main import create_app


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
    assert Path(messages[0]["path"]).read_text(encoding="utf-8").count("Welcome to Prompteer") == 1


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
