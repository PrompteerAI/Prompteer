"""Tests for integration feature kill switches and development route gating."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.api.deps import get_current_principal
from app.core.config import settings
from app.core.security import Principal
from app.db.session import get_session
from app.integrations.payments.mock import STORE
from app.main import create_app
from tests.support import reset_limiter_storage


@pytest.fixture(autouse=True)
def reset_feature_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)
    monkeypatch.setattr(settings, "feature_llm_enabled", True)
    monkeypatch.setattr(settings, "feature_payments_enabled", True)
    monkeypatch.setattr(settings, "feature_email_enabled", True)
    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "google_client_secret", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "sendgrid_api_key", "")
    reset_limiter_storage()
    STORE.reset()


def test_feature_config_endpoint_reflects_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "feature_llm_enabled", False)
    monkeypatch.setattr(settings, "feature_payments_enabled", True)
    monkeypatch.setattr(settings, "feature_email_enabled", False)
    client = TestClient(create_app())

    response = client.get("/api/v1/config/features")

    assert response.status_code == 200
    assert response.json() == {"llm": False, "payments": True, "email": False}


def test_integration_config_endpoint_reports_mock_and_real_modes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "google_client_id", "google-client")
    monkeypatch.setattr(settings, "google_client_secret", "google-secret")
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "anthropic_api_key", "anthropic-key")
    monkeypatch.setattr(settings, "stripe_secret_key", "stripe-key")
    monkeypatch.setattr(settings, "sendgrid_api_key", "")
    client = TestClient(create_app())

    response = client.get("/api/v1/config/integrations")

    assert response.status_code == 200
    assert response.json() == {
        "google_oauth": "real",
        "llm": "real",
        "payments": "real",
        "email": "mock",
    }


def test_disabled_llm_route_returns_problem_details(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "feature_llm_enabled", False)
    client = TestClient(create_app())

    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": "Improve this prompt."}],
        },
    )

    assert_feature_disabled(response)


def test_disabled_challenge_run_returns_problem_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "feature_llm_enabled", False)
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
    app.dependency_overrides[get_current_principal] = override_principal
    client = TestClient(app)

    response = client.post(
        "/api/v1/challenges/example/run",
        json={"prompt": "This prompt is long enough to pass validation."},
    )

    assert_feature_disabled(response)


def test_disabled_payments_route_returns_problem_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "feature_payments_enabled", False)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/billing/checkout",
        json={"customer_email": "paid@prompteer.dev"},
    )

    assert_feature_disabled(response)


def test_disabled_email_route_returns_problem_details(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "feature_email_enabled", False)
    client = TestClient(create_app())

    response = client.post(
        "/v3/mail/send",
        json={
            "personalizations": [{"to": [{"email": "paid@prompteer.dev"}]}],
            "from": {"email": "no-reply@prompteer.dev"},
            "subject": "Disabled",
            "content": [{"type": "text/plain", "value": "Hello"}],
        },
    )

    assert_feature_disabled(response)


def assert_feature_disabled(response: Response) -> None:
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "feature_disabled"
    assert body["type"] == "https://prompteer.dev/errors/feature-disabled"


async def override_principal() -> Principal:
    return Principal(
        subject="mock-google-oauth2|admin",
        email="admin@prompteer.dev",
        is_admin=True,
    )
