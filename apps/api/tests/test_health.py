"""Tests for liveness, readiness, startup, and integration status endpoints."""

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.v1 import health
from app.core.config import settings
from app.core.migrations import MigrationState
from app.main import app


@pytest.fixture(autouse=True)
def reset_health_settings(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)
    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "google_client_secret", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "sendgrid_api_key", "")
    monkeypatch.setattr(settings, "feature_llm_enabled", True)
    monkeypatch.setattr(settings, "feature_payments_enabled", True)
    monkeypatch.setattr(settings, "feature_email_enabled", True)


def test_liveness_probe() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_integrations_default_to_mocks() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/integrations")
    assert response.status_code == 200
    assert response.json() == {
        "llm": "mock",
        "google_oauth": "mock",
        "stripe": "mock",
        "email": "mock",
    }


def test_readiness_probe_reports_ok(monkeypatch: MonkeyPatch) -> None:
    async def ok() -> str:
        return "ok"

    monkeypatch.setattr(health, "check_database", ok)
    monkeypatch.setattr(health, "check_redis", ok)

    client = TestClient(app)
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"
    assert_integration_statuses(
        body,
        {
            "google_oauth": ("ok", "mock"),
            "llm": ("ok", "mock"),
            "stripe": ("ok", "mock"),
            "email": ("ok", "mock"),
        },
    )


def test_readiness_probe_reports_dependency_failure(monkeypatch: MonkeyPatch) -> None:
    async def ok() -> str:
        return "ok"

    async def fail() -> str:
        return "fail"

    monkeypatch.setattr(health, "check_database", ok)
    monkeypatch.setattr(health, "check_redis", fail)

    client = TestClient(app)
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "fail"
    assert_integration_statuses(
        body,
        {
            "google_oauth": ("ok", "mock"),
            "llm": ("ok", "mock"),
            "stripe": ("ok", "mock"),
            "email": ("ok", "mock"),
        },
    )


def test_readiness_probe_reports_mock_integration_failure_without_dev_routes(
    monkeypatch: MonkeyPatch,
) -> None:
    async def ok() -> str:
        return "ok"

    monkeypatch.setattr(health, "check_database", ok)
    monkeypatch.setattr(health, "check_redis", ok)
    monkeypatch.setattr(settings, "enable_dev_routes", False)

    client = TestClient(app)
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert_integration_statuses(
        body,
        {
            "google_oauth": ("fail", "mock"),
            "llm": ("fail", "mock"),
            "stripe": ("fail", "mock"),
            "email": ("fail", "mock"),
        },
    )


def test_readiness_probe_reports_partial_google_credentials(
    monkeypatch: MonkeyPatch,
) -> None:
    async def ok() -> str:
        return "ok"

    monkeypatch.setattr(health, "check_database", ok)
    monkeypatch.setattr(health, "check_redis", ok)
    monkeypatch.setattr(settings, "google_client_id", "google-client")

    client = TestClient(app)
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    google = response.json()["checks"]["integrations"]["google_oauth"]
    assert google["status"] == "fail"
    assert google["mode"] == "partial"


def test_startup_probe_reports_matching_migration_head(monkeypatch: MonkeyPatch) -> None:
    def ok() -> MigrationState:
        return MigrationState(status="ok", current="abc", head="abc")

    monkeypatch.setattr(health, "check_migrations", ok)

    client = TestClient(app)
    response = client.get("/api/v1/health/startup")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "migrations": {
                "status": "ok",
                "current": "abc",
                "head": "abc",
                "detail": None,
            }
        },
    }


def test_startup_probe_reports_stale_migration(monkeypatch: MonkeyPatch) -> None:
    def stale() -> MigrationState:
        return MigrationState(
            status="fail",
            current="old",
            head="new",
            detail="database revision does not match alembic head",
        )

    monkeypatch.setattr(health, "check_migrations", stale)

    client = TestClient(app)
    response = client.get("/api/v1/health/startup")

    assert response.status_code == 503
    assert response.json()["checks"]["migrations"] == {
        "status": "fail",
        "current": "old",
        "head": "new",
        "detail": "database revision does not match alembic head",
    }


def test_dev_mailbox_lists_messages() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/dev/mailbox")
    assert response.status_code == 200
    assert "messages" in response.json()


def assert_integration_statuses(
    body: dict[str, object],
    expected: dict[str, tuple[str, str]],
) -> None:
    checks = body["checks"]
    assert isinstance(checks, dict)
    integrations = checks["integrations"]
    assert isinstance(integrations, dict)
    for name, (status, mode) in expected.items():
        integration = integrations[name]
        assert isinstance(integration, dict)
        assert integration["status"] == status
        assert integration["mode"] == mode
        assert isinstance(integration["detail"], str)
