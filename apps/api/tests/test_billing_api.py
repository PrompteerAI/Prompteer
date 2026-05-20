"""Tests for billing checkout API routes and mock completion behavior."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.ratelimit import limiter
from app.integrations.payments.mock import STORE
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    limiter.reset()
    STORE.reset()


def test_billing_checkout_create_retrieve_and_complete() -> None:
    client = TestClient(create_app())

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"customer_email": "paid@prompteer.dev"},
    )
    assert create_response.status_code == 200
    session = create_response.json()
    assert session["id"].startswith("cs_test_")
    assert session["amount_total"] == 1200
    assert session["currency"] == "usd"
    assert session["provider"] == "mock"
    assert session["status"] == "open"
    assert session["payment_status"] == "unpaid"

    retrieve_response = client.get(f"/api/v1/billing/checkout/{session['id']}")
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["id"] == session["id"]

    complete_response = client.post(f"/api/v1/billing/checkout/{session['id']}/complete")
    assert complete_response.status_code == 200
    completed = complete_response.json()
    assert completed["id"] == session["id"]
    assert completed["status"] == "complete"
    assert completed["payment_status"] == "paid"


def test_billing_checkout_create_is_rate_limited() -> None:
    client = TestClient(create_app())

    for _ in range(5):
        response = client.post(
            "/api/v1/billing/checkout",
            json={"customer_email": "paid@prompteer.dev"},
        )
        assert response.status_code == 200

    limited = client.post(
        "/api/v1/billing/checkout",
        json={"customer_email": "paid@prompteer.dev"},
    )

    assert limited.status_code == 429
    assert limited.headers["content-type"].startswith("application/problem+json")
    assert "retry-after" in limited.headers
    assert limited.json()["code"] == "rate_limited"
