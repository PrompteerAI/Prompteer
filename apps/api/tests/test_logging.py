from pytest import MonkeyPatch

from app.core import logging as api_logging
from app.core.config import settings


def test_log_context_includes_service_version_and_env(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "app_version", "test-version")
    monkeypatch.setattr(settings, "env", "test")

    event = api_logging.add_request_id(None, "info", {})

    assert event["service"] == "prompteer-api"
    assert event["version"] == "test-version"
    assert event["env"] == "test"
    assert "request_id" in event
