"""Tests for Stripe mock checkout sessions, webhooks, and real client payloads."""

import json
from collections.abc import Generator
from urllib.parse import parse_qs

import httpx
import pytest
import respx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

# Import model modules so SQLModel metadata is populated for test databases.
import app.models  # noqa: F401  # Register SQLModel tables before creating test metadata.
from app.core.config import settings
from app.db.session import get_session
from app.integrations.payments import get_payments_client
from app.integrations.payments.base import PaymentsProviderError
from app.integrations.payments.mock import (
    STORE,
    MockStripeClient,
    MockStripeSignatureError,
)
from app.integrations.payments.real import StripeClient
from app.integrations.payments.webhooks import (
    MOCK_STRIPE_WEBHOOK_SECRET,
    construct_stripe_event,
    sign_stripe_webhook_payload,
)
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
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")
    STORE.reset()


def create_mock_stripe_test_app() -> FastAPI:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    return app


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
    client = TestClient(create_mock_stripe_test_app())

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
    assert completed["webhook"]["received"] is True
    assert completed["webhook"]["processed"] is False


def test_mock_stripe_route_rejects_malformed_json_payload() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/checkout/sessions",
        content="{",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["detail"] == "Malformed JSON payload."


def test_mock_stripe_expire_route() -> None:
    client = TestClient(create_mock_stripe_test_app())

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


def test_mock_stripe_uses_default_webhook_secret_for_whitespace_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "stripe_secret_key", "  ")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "  ")

    assert MockStripeClient().webhook_secret() == MOCK_STRIPE_WEBHOOK_SECRET


def test_stripe_webhook_signature_parser_accepts_spaced_segments() -> None:
    payload = json.dumps(
        {
            "id": "evt_mock_spaced",
            "object": "event",
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_spaced", "object": "checkout.session"}},
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    signature = sign_stripe_webhook_payload(
        payload,
        MOCK_STRIPE_WEBHOOK_SECRET,
    ).replace(",", ", ")

    assert construct_stripe_event(payload, signature, MOCK_STRIPE_WEBHOOK_SECRET)["id"] == (
        "evt_mock_spaced"
    )


def test_stripe_webhook_rejects_signed_non_event_payload() -> None:
    payload = json.dumps(
        {"id": "not_evt", "object": "checkout.session", "data": {"object": {}}},
        separators=(",", ":"),
        sort_keys=True,
    )
    signature = sign_stripe_webhook_payload(payload, MOCK_STRIPE_WEBHOOK_SECRET)

    with pytest.raises(MockStripeSignatureError, match="not a Stripe event"):
        construct_stripe_event(payload, signature, MOCK_STRIPE_WEBHOOK_SECRET)


def test_payments_factory_selects_real_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")
    assert isinstance(get_payments_client(), StripeClient)

    monkeypatch.setattr(settings, "stripe_secret_key", "")
    assert isinstance(get_payments_client(), MockStripeClient)


def test_payments_factory_treats_whitespace_key_as_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "stripe_secret_key", "   ")

    assert isinstance(get_payments_client(), MockStripeClient)


def test_mock_stripe_routes_are_not_available_in_real_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")
    client = TestClient(create_mock_stripe_test_app())

    response = client.post("/v1/checkout/sessions", json=CHECKOUT_PAYLOAD)

    assert response.status_code == 404


def test_mock_stripe_routes_hide_malformed_requests_in_real_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test")
    client = TestClient(create_mock_stripe_test_app())

    assert client.post("/v1/checkout/sessions").status_code == 404
    assert client.get("/dev/stripe/complete").status_code == 404
    assert client.post("/api/v1/billing/checkout/cs_test_mock/complete").status_code == 404


def test_mock_stripe_routes_hide_when_dev_routes_are_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "enable_dev_routes", False)
    client = TestClient(create_mock_stripe_test_app())

    assert client.post("/v1/checkout/sessions").status_code == 404
    assert client.get("/dev/stripe/complete").status_code == 404
    assert client.post("/api/v1/billing/checkout/cs_test_mock/complete").status_code == 404


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (402, "Your card was declined."),
        (500, "An internal server error occurred."),
    ],
)
async def test_stripe_real_client_wraps_checkout_http_errors(
    status_code: int,
    message: str,
) -> None:
    with respx.mock:
        route = respx.post("https://stripe.example/v1/checkout/sessions").mock(
            return_value=httpx.Response(
                status_code,
                json={
                    "error": {
                        "type": "api_error",
                        "code": "provider_error",
                        "message": message,
                    }
                },
            )
        )
        client = StripeClient(api_key="sk_test", base_url="https://stripe.example")

        with pytest.raises(PaymentsProviderError) as exc_info:
            await client.create_checkout_session(CHECKOUT_PAYLOAD)

    assert route.called
    error = exc_info.value
    assert error.provider == "stripe"
    assert error.status_code == status_code
    assert error.detail == f"stripe provider returned HTTP {status_code}. {message}"


@pytest.mark.asyncio
async def test_stripe_real_client_wraps_checkout_transport_errors() -> None:
    with respx.mock:
        route = respx.post("https://stripe.example/v1/checkout/sessions").mock(
            side_effect=httpx.ConnectError("network down")
        )
        client = StripeClient(api_key="sk_test", base_url="https://stripe.example")

        with pytest.raises(PaymentsProviderError) as exc_info:
            await client.create_checkout_session(CHECKOUT_PAYLOAD)

    assert route.called
    error = exc_info.value
    assert error.provider == "stripe"
    assert error.status_code is None
    assert error.detail == "stripe provider is unavailable."
