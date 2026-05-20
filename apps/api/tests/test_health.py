from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.v1 import health
from app.core.migrations import MigrationState
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
