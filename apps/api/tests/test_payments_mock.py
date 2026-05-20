import json
from urllib.parse import parse_qs

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations.payments import get_payments_client
from app.integrations.payments.mock import (
    MOCK_STRIPE_WEBHOOK_SECRET,
    STORE,
    MockStripeClient,
    MockStripeSignatureError,
)
from app.integrations.payments.real import StripeClient
from app.main import create_app

CHECKOUT_PAYLOAD = {
    "mode": "subscription",
    "success_url": "http://localhost:3000/en/billing/success?session_id={CHECKOUT_SESSION_ID}",
    "cancel_url": "http://localhost:3000/en/billing",
    "customer_email": "paid@prompteer.dev",
    "metadata": {"user_id": "00000000-0000-4000-8000-000000000002"},
    "line_items": [
        {
            "quantity": 1,
            "price_data": {
                "currency": "usd",
                "unit_amount": 1200,
                "recurring": {"interval": "month"},
                "product_data": {"name": "Prompteer Pro"},
            },
        }
    ],
}


@pytest.fixture(autouse=True)
def reset_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")
    STORE.reset()


@pytest.mark.asyncio
async def test_mock_stripe_session_lifecycle_and_webhook_signature() -> None:
    client = MockStripeClient()

    session = await client.create_checkout_session(CHECKOUT_PAYLOAD)
    assert session["id"].startswith("cs_test_")
    assert session["object"] == "checkout.session"
    assert session["status"] == "open"
    assert session["payment_status"] == "unpaid"
    assert session["amount_total"] == 1200
    assert session["currency"] == "usd"
    assert session["mode"] == "subscription"
    assert session["metadata"] == {"user_id": "00000000-0000-4000-8000-000000000002"}
    assert session["url"].startswith("https://checkout.stripe.com/c/pay/")

    completed = await client.complete_checkout_session(session["id"])
    completed_session = completed["session"]
    assert completed_session["status"] == "complete"
    assert completed_session["payment_status"] == "paid"
    assert completed_session["subscription"].startswith("sub_mock_")
    assert completed["event"]["type"] == "checkout.session.completed"

    payload = json.dumps(completed["event"], separators=(",", ":"), sort_keys=True)
    signature = client.sign_webhook_payload(payload)
    assert client.construct_event(payload, signature)["id"] == completed["event"]["id"]

    with pytest.raises(MockStripeSignatureError):
        client.construct_event(payload, "t=1800000000,v1=bad")


def test_mock_stripe_routes_accept_form_payload_and_complete_checkout() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/v1/checkout/sessions",
        data={
            "mode": "payment",
            "success_url": "http://localhost:3000/en/billing/success",
            "cancel_url": "http://localhost:3000/en/billing",
            "customer_email": "free@prompteer.dev",
            "metadata[user_id]": "00000000-0000-4000-8000-000000000003",
            "line_items[0][quantity]": "2",
            "line_items[0][price_data][currency]": "usd",
            "line_items[0][price_data][unit_amount]": "900",
            "line_items[0][price_data][product_data][name]": "Prompt credits",
        },
    )
    assert create_response.status_code == 200
    session = create_response.json()
    assert session["amount_total"] == 1800
    assert session["currency"] == "usd"
    assert session["metadata"]["user_id"] == "00000000-0000-4000-8000-000000000003"

    retrieve_response = client.get(f"/v1/checkout/sessions/{session['id']}")
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["id"] == session["id"]

    complete_response = client.get("/dev/stripe/complete", params={"session_id": session["id"]})
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["session"]["status"] == "complete"
    assert completed["session"]["payment_intent"].startswith("pi_mock_")
    assert completed["event"]["type"] == "checkout.session.completed"
    assert completed["webhook_signature"].startswith("t=")


def test_mock_stripe_expire_route() -> None:
    client = TestClient(create_app())

    session = client.post("/v1/checkout/sessions", json=CHECKOUT_PAYLOAD).json()
    expire_response = client.post(f"/v1/checkout/sessions/{session['id']}/expire")

    assert expire_response.status_code == 200
    expired = expire_response.json()
    assert expired["status"] == "expired"
    assert expired["payment_status"] == "unpaid"
    assert expired["url"] is None

    complete_response = client.get("/dev/stripe/complete", params={"session_id": session["id"]})
    assert complete_response.status_code == 400


def test_mock_stripe_uses_default_webhook_secret_when_env_is_empty() -> None:
    client = MockStripeClient()
    assert client.webhook_secret() == MOCK_STRIPE_WEBHOOK_SECRET


def test_payments_factory_selects_real_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")
    assert isinstance(get_payments_client(), StripeClient)

    monkeypatch.setattr(settings, "stripe_secret_key", "")
    assert isinstance(get_payments_client(), MockStripeClient)


@pytest.mark.asyncio
async def test_stripe_real_client_posts_checkout_form_payload() -> None:
    expected = {
        "id": "cs_test_real",
        "object": "checkout.session",
        "mode": "subscription",
        "status": "open",
        "payment_status": "unpaid",
        "amount_total": 1200,
        "currency": "usd",
        "url": "https://checkout.stripe.com/c/pay/cs_test_real",
    }
    with respx.mock:
        route = respx.post("https://stripe.example/v1/checkout/sessions").mock(
            return_value=httpx.Response(200, json=expected)
        )
        client = StripeClient(api_key="sk_test", base_url="https://stripe.example")

        result = await client.create_checkout_session(CHECKOUT_PAYLOAD)

    assert result == expected
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer sk_test"
    form = parse_qs(request.content.decode("utf-8"))
    assert form["mode"] == ["subscription"]
    assert form["customer_email"] == ["paid@prompteer.dev"]
    assert form["metadata[user_id]"] == ["00000000-0000-4000-8000-000000000002"]
    assert form["line_items[0][price_data][unit_amount]"] == ["1200"]
