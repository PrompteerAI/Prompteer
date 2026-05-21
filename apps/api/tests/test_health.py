"""Tests for liveness, readiness, startup, and integration status endpoints."""

from typing import Literal

import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.v1 import health
from app.core.config import settings
from app.core.migrations import MigrationState
from app.main import app


def dependency_check(
    status: Literal["ok", "fail"],
    detail: str | None = None,
) -> health.DependencyCheck:
    return {"status": status, "detail": detail or f"test dependency {status}."}


@pytest.fixture(autouse=True)
def reset_health_settings(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)
    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "google_client_secret", "")
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")
    monkeypatch.setattr(settings, "sendgrid_api_key", "")
    monkeypatch.setattr(settings, "feature_llm_enabled", True)
    monkeypatch.setattr(settings, "feature_payments_enabled", True)
    monkeypatch.setattr(settings, "feature_email_enabled", True)


@pytest.fixture
def healthy_required_dependencies(monkeypatch: MonkeyPatch) -> None:
    async def ok() -> health.DependencyCheck:
        return dependency_check("ok")

    monkeypatch.setattr(health, "check_database", ok)
    monkeypatch.setattr(health, "check_redis", ok)


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
    async def ok() -> health.DependencyCheck:
        return dependency_check("ok")

    monkeypatch.setattr(health, "check_database", ok)
    monkeypatch.setattr(health, "check_redis", ok)

    client = TestClient(app)
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == dependency_check("ok")
    assert body["checks"]["redis"] == dependency_check("ok")
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
    async def ok() -> health.DependencyCheck:
        return dependency_check("ok")

    async def fail() -> health.DependencyCheck:
        return dependency_check("fail")

    monkeypatch.setattr(health, "check_database", ok)
    monkeypatch.setattr(health, "check_redis", fail)

    client = TestClient(app)
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == dependency_check("ok")
    assert body["checks"]["redis"] == dependency_check("fail")
    assert_integration_statuses(
        body,
        {
            "google_oauth": ("ok", "mock"),
            "llm": ("ok", "mock"),
            "stripe": ("ok", "mock"),
            "email": ("ok", "mock"),
        },
    )


def test_readiness_probe_reports_real_redis_connection_failure(
    monkeypatch: MonkeyPatch,
) -> None:
    async def ok() -> health.DependencyCheck:
        return dependency_check("ok")

    monkeypatch.setattr(health, "check_database", ok)
    monkeypatch.setattr(settings, "redis_url", "redis://127.0.0.1:1/0")

    client = TestClient(app)
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == dependency_check("ok")
    assert body["checks"]["redis"]["status"] == "fail"
    assert isinstance(body["checks"]["redis"]["detail"], str)
    assert "Redis ping failed" in body["checks"]["redis"]["detail"]
    assert_integration_statuses(
        body,
        {
            "google_oauth": ("ok", "mock"),
            "llm": ("ok", "mock"),
            "stripe": ("ok", "mock"),
            "email": ("ok", "mock"),
        },
    )


def test_readiness_probe_reports_all_real_integrations_ok(
    monkeypatch: MonkeyPatch,
    healthy_required_dependencies: None,
) -> None:
    monkeypatch.setattr(settings, "google_client_id", "google-client")
    monkeypatch.setattr(settings, "google_client_secret", "google-secret")
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(settings, "openai_base_url", "https://openai.example/v1")
    monkeypatch.setattr(settings, "openai_chat_model", "gpt-health")
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_stripe")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr(settings, "sendgrid_api_key", "SG.test")

    with respx.mock(assert_all_mocked=True, assert_all_called=False) as router:
        google_discovery = router.get(
            "https://accounts.google.com/.well-known/openid-configuration"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "issuer": "https://accounts.google.com",
                    "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_endpoint": "https://oauth2.googleapis.com/token",
                    "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
                    "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
                },
            )
        )
        google_jwks = router.get("https://www.googleapis.com/oauth2/v3/certs").mock(
            return_value=httpx.Response(
                200,
                json={
                    "keys": [
                        {
                            "kid": "test-key",
                            "kty": "RSA",
                            "alg": "RS256",
                            "use": "sig",
                            "n": "test-modulus",
                            "e": "AQAB",
                        }
                    ]
                },
            )
        )
        openai_model = router.get("https://openai.example/v1/models/gpt-health").mock(
            return_value=httpx.Response(
                200,
                json={"id": "gpt-health", "object": "model", "owned_by": "openai"},
            )
        )
        stripe_balance = router.get("https://api.stripe.com/v1/balance").mock(
            return_value=httpx.Response(
                200,
                json={
                    "object": "balance",
                    "available": [],
                    "pending": [],
                    "livemode": False,
                },
            )
        )
        sendgrid_scopes = router.get("https://api.sendgrid.com/v3/scopes").mock(
            return_value=httpx.Response(200, json={"scopes": ["mail.send"]})
        )

        client = TestClient(app)
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert_integration_statuses(
        body,
        {
            "google_oauth": ("ok", "real"),
            "llm": ("ok", "real"),
            "stripe": ("ok", "real"),
            "email": ("ok", "real"),
        },
    )
    assert google_discovery.called
    assert google_jwks.called
    assert openai_model.called
    assert stripe_balance.called
    assert sendgrid_scopes.called


def test_readiness_probe_reports_real_stripe_missing_webhook_secret(
    monkeypatch: MonkeyPatch,
    healthy_required_dependencies: None,
) -> None:
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_stripe")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "")

    with respx.mock(assert_all_mocked=True, assert_all_called=False) as router:
        stripe_balance = router.get("https://api.stripe.com/v1/balance").mock(
            return_value=httpx.Response(
                200,
                json={"object": "balance", "available": [], "pending": []},
            )
        )

        client = TestClient(app)
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    stripe = body["checks"]["integrations"]["stripe"]
    assert stripe["status"] == "fail"
    assert stripe["mode"] == "real"
    assert "STRIPE_WEBHOOK_SECRET is required" in stripe["detail"]
    assert not stripe_balance.called


def test_readiness_probe_reports_real_anthropic_provider_ok(
    monkeypatch: MonkeyPatch,
    healthy_required_dependencies: None,
) -> None:
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-test")
    monkeypatch.setattr(settings, "anthropic_base_url", "https://anthropic.example/v1")
    monkeypatch.setattr(settings, "anthropic_model", "claude-health")

    with respx.mock(assert_all_mocked=True, assert_all_called=False) as router:
        count_tokens = router.post("https://anthropic.example/v1/messages/count_tokens").mock(
            return_value=httpx.Response(200, json={"input_tokens": 3})
        )

        client = TestClient(app)
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["checks"]["integrations"]["llm"]["status"] == "ok"
    assert body["checks"]["integrations"]["llm"]["mode"] == "real"
    assert count_tokens.called


def test_readiness_probe_reports_real_provider_http_failure(
    monkeypatch: MonkeyPatch,
    healthy_required_dependencies: None,
) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(settings, "openai_base_url", "https://openai.example/v1")
    monkeypatch.setattr(settings, "openai_chat_model", "gpt-health")

    with respx.mock(assert_all_mocked=True, assert_all_called=False) as router:
        openai_model = router.get("https://openai.example/v1/models/gpt-health").mock(
            return_value=httpx.Response(
                503,
                json={"error": {"message": "provider unavailable"}},
            )
        )

        client = TestClient(app)
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["integrations"]["llm"]["status"] == "fail"
    assert body["checks"]["integrations"]["llm"]["mode"] == "real"
    assert "503" in body["checks"]["integrations"]["llm"]["detail"]
    assert openai_model.called


def test_readiness_probe_reports_mock_integration_failure_without_dev_routes(
    monkeypatch: MonkeyPatch,
) -> None:
    async def ok() -> health.DependencyCheck:
        return dependency_check("ok")

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
    async def ok() -> health.DependencyCheck:
        return dependency_check("ok")

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
