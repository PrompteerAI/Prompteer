from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.v1 import health
from app.main import app


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
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "redis": "ok", "integrations": "configured"},
    }


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
    assert response.json() == {
        "status": "degraded",
        "checks": {"database": "ok", "redis": "fail", "integrations": "configured"},
    }
