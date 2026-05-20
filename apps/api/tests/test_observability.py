# Tests for optional Sentry initialization and unhandled Problem Details responses.
# They prove empty DSNs stay local while configured DSNs call the SDK boundary.

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core import observability
from app.core.config import settings
from app.main import create_app


class FakeSentry:
    def __init__(self) -> None:
        self.init_kwargs: dict[str, object] | None = None
        self.captured: list[BaseException] = []
        self.tags: dict[str, str] = {}

    def init(self, **kwargs: object) -> object:
        self.init_kwargs = kwargs
        return None

    def capture_exception(self, error: BaseException) -> object:
        self.captured.append(error)
        return None

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


def test_observability_stays_disabled_without_sentry_dsn(monkeypatch: MonkeyPatch) -> None:
    fake_sentry = FakeSentry()
    monkeypatch.setattr(settings, "sentry_dsn", "")
    monkeypatch.setattr(observability, "import_sentry_sdk", lambda: fake_sentry)

    observability.init_observability()
    observability.capture_exception(RuntimeError("not reported"))

    assert fake_sentry.init_kwargs is None
    assert fake_sentry.captured == []


def test_observability_initializes_sentry_when_dsn_is_configured(
    monkeypatch: MonkeyPatch,
) -> None:
    fake_sentry = FakeSentry()
    integration = object()
    monkeypatch.setattr(settings, "sentry_dsn", "https://public@example.ingest.sentry.io/1")
    monkeypatch.setattr(settings, "env", "test")
    monkeypatch.setattr(settings, "app_version", "test-version")
    monkeypatch.setattr(observability, "import_sentry_sdk", lambda: fake_sentry)
    monkeypatch.setattr(observability, "import_fastapi_integration", lambda: integration)

    error = RuntimeError("reported")
    observability.init_observability()
    observability.capture_exception(error)

    assert fake_sentry.init_kwargs == {
        "dsn": "https://public@example.ingest.sentry.io/1",
        "environment": "test",
        "release": "test-version",
        "integrations": [integration],
        "send_default_pii": False,
        "traces_sample_rate": 1.0,
        "enable_logs": True,
    }
    assert fake_sentry.tags == {
        "service": "prompteer-api",
        "version": "test-version",
    }
    assert fake_sentry.captured == [error]


def test_unhandled_api_errors_return_problem_details_and_capture_sentry(
    monkeypatch: MonkeyPatch,
) -> None:
    captured: list[BaseException] = []
    monkeypatch.setattr("app.core.errors.capture_exception", captured.append)

    @asynccontextmanager
    async def no_lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield

    app = create_app()
    app.router.lifespan_context = no_lifespan

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/boom", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    body: dict[str, Any] = response.json()
    assert body["type"] == "https://prompteer.dev/errors/internal-server-error"
    assert body["code"] == "internal_server_error"
    assert body["request_id"] == "test-request-id"
    assert captured
