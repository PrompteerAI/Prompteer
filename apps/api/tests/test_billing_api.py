"""Tests for billing checkout API routes and mock completion behavior."""

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.core.config import settings
from app.db.seed import seed
from app.db.session import get_session
from app.integrations.payments.mock import STORE
from app.main import create_app
from app.models.domain import User
from tests.support import reset_limiter_storage


@pytest.fixture(autouse=True)
def reset_store(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    reset_limiter_storage()
    STORE.reset()


def test_billing_checkout_create_retrieve_and_complete() -> None:
    app = create_billing_test_app()
    client = TestClient(app)

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


def test_mock_checkout_completion_updates_user_plan() -> None:
    app = create_billing_test_app(initial_paid_plan="free")
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/billing/checkout",
        json={"customer_email": "paid@prompteer.dev"},
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
    return app
