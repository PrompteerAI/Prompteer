"""Tests for billing checkout API routes and mock completion behavior."""

import asyncio
import json
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import app.integrations.payments as payments_integration
import app.models  # noqa: F401  # Register SQLModel tables before creating test metadata.
from app.api.deps import get_current_principal
from app.core.config import settings
from app.core.security import Principal
from app.db.seed import seed
from app.db.session import get_session
from app.integrations.email import mock as email_mock
from app.integrations.payments.base import PaymentsProviderError
from app.integrations.payments.mock import STORE, MockStripeClient
from app.integrations.payments.webhooks import (
    MOCK_STRIPE_WEBHOOK_SECRET,
    sign_stripe_webhook_payload,
)
from app.main import create_app
from app.models.domain import StripeCheckoutSession, StripeWebhookEvent, User
from tests.support import reset_limiter_storage


@pytest.fixture(autouse=True)
def reset_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")
    reset_limiter_storage()
    STORE.reset()


def test_billing_checkout_create_retrieve_and_complete() -> None:
    app = create_billing_test_app()
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200
    session = create_response.json()
    assert session["id"].startswith("cs_test_")
    assert session["amount_total"] == 1200
    assert session["currency"] == "usd"
    assert session["provider"] == "mock"
    assert session["status"] == "open"
    assert session["payment_status"] == "unpaid"
    with Session(app.state.test_engine) as assertion_session:
        checkout_record = assertion_session.get(StripeCheckoutSession, session["id"])
    assert checkout_record is not None
    assert checkout_record.user_id == "00000000-0000-4000-8000-000000000002"
    assert checkout_record.amount_total == 1200

    retrieve_response = client.get(f"/api/v1/billing/checkout/{session['id']}")
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["id"] == session["id"]

    complete_response = client.post(f"/api/v1/billing/checkout/{session['id']}/complete")
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["id"] == session["id"]
    assert completed["status"] == "complete"
    assert completed["payment_status"] == "paid"


def test_billing_checkout_requires_authentication() -> None:
    app = create_billing_test_app()
    app.dependency_overrides.pop(get_current_principal, None)
    client = TestClient(app)

    response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )

    assert response.status_code == 401


def test_billing_checkout_returns_problem_details_for_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = create_billing_test_app()
    monkeypatch.setattr(
        payments_integration,
        "get_payments_client",
        lambda: FailingStripeClient(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )

    assert response.status_code == 502
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = response.json()
    assert problem["code"] == "payments_provider_error"
    assert problem["title"] == "Payments Provider Error"
    assert problem["detail"] == "stripe provider returned HTTP 500. provider unavailable"


def test_checkout_create_ignores_spoofed_legacy_customer_email() -> None:
    app = create_billing_test_app()
    client = TestClient(app)
    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"customer_email": "admin@prompteer.dev"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    assert create_response.json()["customer_email"] == "paid@prompteer.dev"
    with Session(app.state.test_engine) as assertion_session:
        checkout_record = assertion_session.get(StripeCheckoutSession, session_id)
    assert checkout_record is not None
    assert checkout_record.customer_email == "paid@prompteer.dev"
    assert checkout_record.user_id == "00000000-0000-4000-8000-000000000002"

    app.dependency_overrides[get_current_principal] = override_admin_principal

    retrieve_response = client.get(f"/api/v1/billing/checkout/{session_id}")
    complete_response = client.post(f"/api/v1/billing/checkout/{session_id}/complete")

    assert retrieve_response.status_code == 404
    assert complete_response.status_code == 404


def test_mock_checkout_completion_updates_user_plan() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200

    complete_response = client.post(
        f"/api/v1/billing/checkout/{create_response.json()['id']}/complete"
    )

    assert complete_response.status_code == 200
    with Session(app.state.test_engine) as assertion_session:
        paid_user = assertion_session.exec(
            select(User).where(User.email == "paid@prompteer.dev")
        ).one()
    assert paid_user.plan == "paid"


def test_dev_stripe_complete_processes_recorded_checkout_webhook() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    complete_response = client.get("/dev/stripe/complete", params={"session_id": session_id})

    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["session"]["id"] == session_id
    assert completed["session"]["status"] == "complete"
    assert completed["session"]["payment_status"] == "paid"
    assert completed["webhook_signature"].startswith("t=")
    assert completed["webhook"]["received"] is True
    assert completed["webhook"]["event_type"] == "checkout.session.completed"
    assert completed["webhook"]["processed"] is True
    assert completed["webhook"]["customer_email"] == "paid@prompteer.dev"

    with Session(app.state.test_engine) as assertion_session:
        paid_user = assertion_session.exec(
            select(User).where(User.email == "paid@prompteer.dev")
        ).one()
        checkout_record = assertion_session.get(StripeCheckoutSession, session_id)
        webhook_events = assertion_session.exec(select(StripeWebhookEvent)).all()
    assert paid_user.plan == "paid"
    assert checkout_record is not None
    assert checkout_record.status == "complete"
    assert checkout_record.payment_status == "paid"
    assert len(webhook_events) == 1
    assert webhook_events[0].event_id == completed["event"]["id"]
    assert webhook_events[0].processed is True


def test_mock_checkout_completion_captures_receipt_email(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mailbox_dir = tmp_path / "mailbox"
    monkeypatch.setattr(settings, "mock_mailbox_dir", str(mailbox_dir))
    monkeypatch.setattr(email_mock, "default_mailbox_dir", lambda: mailbox_dir)
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]

    complete_response = client.post(f"/api/v1/billing/checkout/{session_id}/complete")

    assert complete_response.status_code == 200
    receipts = [
        path.read_text(encoding="utf-8")
        for path in sorted(mailbox_dir.glob("*paid@prompteer.dev.eml"))
    ]
    receipt_text = next(text for text in receipts if "Subject: Prompteer Pro receipt" in text)
    assert "Subject: Prompteer Pro receipt" in receipt_text
    assert session_id in receipt_text
    assert "checkout.session.completed" in receipt_text


def test_billing_subscription_reflects_current_user_plan_after_checkout() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        subject="mock-google-oauth2|paid",
        email="paid@prompteer.dev",
    )
    client = TestClient(app)

    initial_response = client.get("/api/v1/billing/subscription")

    assert initial_response.status_code == 200
    initial_subscription = initial_response.json()
    assert initial_subscription["customer_email"] == "paid@prompteer.dev"
    assert initial_subscription["plan"] == "free"
    assert initial_subscription["status"] == "inactive"
    assert initial_subscription["provider"] == "mock"

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200
    complete_response = client.post(
        f"/api/v1/billing/checkout/{create_response.json()['id']}/complete"
    )
    assert complete_response.status_code == 200

    current_response = client.get("/api/v1/billing/subscription")

    assert current_response.status_code == 200
    current_subscription = current_response.json()
    assert current_subscription["plan"] == "paid"
    assert current_subscription["status"] == "active"


def test_stripe_webhook_updates_user_plan() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200
    completion = asyncio.run(
        MockStripeClient().complete_checkout_session(create_response.json()["id"])
    )
    payload = json.dumps(completion["event"], separators=(",", ":"), sort_keys=True)
    signature = MockStripeClient().sign_webhook_payload(payload)

    webhook_response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert webhook_response.status_code == 200
    webhook = webhook_response.json()
    assert webhook["received"] is True
    assert webhook["event_type"] == "checkout.session.completed"
    assert webhook["processed"] is True
    assert webhook["customer_email"] == "paid@prompteer.dev"
    with Session(app.state.test_engine) as assertion_session:
        paid_user = assertion_session.exec(
            select(User).where(User.email == "paid@prompteer.dev")
        ).one()
    assert paid_user.plan == "paid"


def test_stripe_webhook_captures_receipt_email(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mailbox_dir = tmp_path / "mailbox"
    monkeypatch.setattr(settings, "mock_mailbox_dir", str(mailbox_dir))
    monkeypatch.setattr(email_mock, "default_mailbox_dir", lambda: mailbox_dir)
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200
    session_id = create_response.json()["id"]
    completion = asyncio.run(MockStripeClient().complete_checkout_session(session_id))
    payload = json.dumps(completion["event"], separators=(",", ":"), sort_keys=True)
    signature = MockStripeClient().sign_webhook_payload(payload)

    webhook_response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert webhook_response.status_code == 200
    receipts = [
        path.read_text(encoding="utf-8")
        for path in sorted(mailbox_dir.glob("*paid@prompteer.dev.eml"))
    ]
    receipt_text = next(text for text in receipts if "Subject: Prompteer Pro receipt" in text)
    assert session_id in receipt_text
    assert webhook_response.json()["event_id"] in receipt_text


def test_stripe_webhook_delivery_is_idempotent() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200
    completion = asyncio.run(
        MockStripeClient().complete_checkout_session(create_response.json()["id"])
    )
    payload = json.dumps(completion["event"], separators=(",", ":"), sort_keys=True)
    signature = MockStripeClient().sign_webhook_payload(payload)

    first_response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )
    second_response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert first_response.status_code == 200
    assert first_response.json()["processed"] is True
    assert second_response.status_code == 200
    assert second_response.json()["processed"] is False
    with Session(app.state.test_engine) as assertion_session:
        webhook_events = assertion_session.exec(select(StripeWebhookEvent)).all()
        paid_user = assertion_session.exec(
            select(User).where(User.email == "paid@prompteer.dev")
        ).one()
    assert len(webhook_events) == 1
    assert webhook_events[0].event_id == completion["event"]["id"]
    assert paid_user.plan == "paid"


def test_stripe_webhook_rejects_invalid_signature() -> None:
    client = TestClient(create_billing_test_app())

    response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content='{"id":"evt_bad","type":"checkout.session.completed"}',
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "t=1800000000,v1=bad",
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "bad_request"


def test_real_stripe_mode_requires_webhook_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(create_billing_test_app())
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_live_test")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")
    event = {
        "id": "evt_missing_real_secret",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {"object": {"customer_email": "paid@prompteer.dev"}},
    }
    payload = json.dumps(event, separators=(",", ":"), sort_keys=True)
    signature = sign_stripe_webhook_payload(payload, MOCK_STRIPE_WEBHOOK_SECRET)

    response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "STRIPE_WEBHOOK_SECRET is required" in response.json()["detail"]


def test_stripe_webhook_rejects_non_utf8_payload() -> None:
    client = TestClient(create_billing_test_app())

    response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=b"\xff",
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "t=1800000000,v1=bad",
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "bad_request"
    assert "UTF-8" in response.json()["detail"]


def test_stripe_webhook_matches_customer_email_case_insensitively() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)
    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )
    assert create_response.status_code == 200
    completion = asyncio.run(
        MockStripeClient().complete_checkout_session(create_response.json()["id"])
    )
    event = completion["event"]
    event["id"] = "evt_case_insensitive"
    event["data"]["object"]["customer_email"] = "PAID@PROMPTEER.DEV"
    payload = json.dumps(event, separators=(",", ":"), sort_keys=True)
    signature = MockStripeClient().sign_webhook_payload(payload)

    response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert response.status_code == 200
    webhook = response.json()
    assert webhook["processed"] is True
    assert webhook["customer_email"] == "paid@prompteer.dev"
    with Session(app.state.test_engine) as assertion_session:
        paid_user = assertion_session.exec(
            select(User).where(User.email == "paid@prompteer.dev")
        ).one()
    assert paid_user.plan == "paid"


def test_stripe_webhook_rejects_unknown_local_checkout_session() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)
    event = {
        "id": "evt_unknown_local_checkout",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_not_created_by_app",
                "mode": "subscription",
                "status": "complete",
                "payment_status": "paid",
                "amount_total": 1200,
                "currency": "usd",
                "customer_email": "paid@prompteer.dev",
                "client_reference_id": "00000000-0000-4000-8000-000000000002",
                "metadata": {"user_id": "00000000-0000-4000-8000-000000000002"},
            }
        },
    }
    payload = json.dumps(event, separators=(",", ":"), sort_keys=True)
    signature = MockStripeClient().sign_webhook_payload(payload)

    response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert response.status_code == 200
    webhook = response.json()
    assert webhook["processed"] is False
    assert webhook["customer_email"] == "paid@prompteer.dev"
    with Session(app.state.test_engine) as assertion_session:
        paid_user = assertion_session.exec(
            select(User).where(User.email == "paid@prompteer.dev")
        ).one()
    assert paid_user.plan == "free"


def test_stripe_webhook_rejects_email_only_checkout_session() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)
    event = {
        "id": "evt_email_only",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {"object": {"customer_email": "paid@prompteer.dev"}},
    }
    payload = json.dumps(event, separators=(",", ":"), sort_keys=True)
    signature = MockStripeClient().sign_webhook_payload(payload)

    response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert response.status_code == 200
    webhook = response.json()
    assert webhook["processed"] is False
    assert webhook["customer_email"] == "paid@prompteer.dev"
    with Session(app.state.test_engine) as assertion_session:
        paid_user = assertion_session.exec(
            select(User).where(User.email == "paid@prompteer.dev")
        ).one()
    assert paid_user.plan == "free"


def test_stripe_webhook_rejects_mismatched_user_metadata() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)
    event = {
        "id": "evt_mismatched_user_metadata",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer_email": "paid@prompteer.dev",
                "metadata": {"user_id": "00000000-0000-4000-8000-000000000001"},
            }
        },
    }
    payload = json.dumps(event, separators=(",", ":"), sort_keys=True)
    signature = MockStripeClient().sign_webhook_payload(payload)

    response = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": signature,
        },
    )

    assert response.status_code == 200
    webhook = response.json()
    assert webhook["processed"] is False
    assert webhook["customer_email"] == "paid@prompteer.dev"
    with Session(app.state.test_engine) as assertion_session:
        paid_user = assertion_session.exec(
            select(User).where(User.email == "paid@prompteer.dev")
        ).one()
    assert paid_user.plan == "free"


def test_billing_checkout_create_is_rate_limited() -> None:
    client = TestClient(create_billing_test_app())

    for _ in range(5):
        response = client.post(
            "/api/v1/billing/checkout",
            json={"plan": "pro_monthly"},
        )
        assert response.status_code == 200

    limited = client.post(
        "/api/v1/billing/checkout",
        json={"plan": "pro_monthly"},
    )

    assert limited.status_code == 429
    assert limited.headers["content-type"].startswith("application/problem+json")
    assert "retry-after" in limited.headers
    assert limited.json()["code"] == "rate_limited"


def create_billing_test_app(*, initial_paid_plan: str = "paid") -> FastAPI:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as seed_session:
        seed(seed_session)
        paid_user = seed_session.exec(select(User).where(User.email == "paid@prompteer.dev")).one()
        paid_user.plan = initial_paid_plan
        seed_session.add(paid_user)
        seed_session.commit()

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.state.test_engine = engine
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_principal] = override_paid_principal
    return app


async def override_paid_principal() -> Principal:
    return Principal(
        subject="mock-google-oauth2|paid",
        email="paid@prompteer.dev",
    )


async def override_admin_principal() -> Principal:
    return Principal(
        subject="mock-google-oauth2|admin",
        email="admin@prompteer.dev",
        is_admin=True,
    )


class FailingStripeClient:
    provider = "stripe"

    async def create_checkout_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        del payload
        raise PaymentsProviderError(
            provider=self.provider,
            detail="stripe provider returned HTTP 500. provider unavailable",
            status_code=500,
        )

    async def retrieve_checkout_session(self, session_id: str) -> dict[str, Any]:
        del session_id
        raise AssertionError("retrieve_checkout_session should not be called")

    async def expire_checkout_session(self, session_id: str) -> dict[str, Any]:
        del session_id
        raise AssertionError("expire_checkout_session should not be called")
