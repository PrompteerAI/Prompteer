"""Tests for structured logging fields and stdlib log bridging."""

import json
import logging
import warnings

from pytest import CaptureFixture, MonkeyPatch

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


def test_console_exception_logging_does_not_preformat_tracebacks(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr(settings, "log_json", False)
    monkeypatch.setattr(settings, "env", "test")
    monkeypatch.setattr(settings, "app_version", "test-version")

    api_logging.configure_logging()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            raise RuntimeError("startup failed")
        except RuntimeError:
            logging.getLogger("uvicorn.error").exception("server_failed")

    output = capsys.readouterr().out
    assert "server_failed" in output
    assert "RuntimeError" in output
    assert not any("format_exc_info" in str(warning.message) for warning in caught)


def test_json_exception_logging_uses_structured_tracebacks(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr(settings, "log_json", True)
    monkeypatch.setattr(settings, "env", "test")
    monkeypatch.setattr(settings, "app_version", "test-version")

    api_logging.configure_logging()
    try:
        raise RuntimeError("startup failed")
    except RuntimeError:
        logging.getLogger("uvicorn.error").exception("server_failed")

    lines = [line for line in capsys.readouterr().out.splitlines() if line]
    event = json.loads(lines[-1])
    assert event["event"] == "server_failed"
    assert event["exception"][0]["exc_type"] == "RuntimeError"


def test_stdlib_logs_use_structlog_processor_formatter(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr(settings, "log_json", True)
    monkeypatch.setattr(settings, "env", "test")
    monkeypatch.setattr(settings, "app_version", "test-version")

    api_logging.configure_logging()
    logging.getLogger("uvicorn.error").info("server_ready")

    lines = [line for line in capsys.readouterr().out.splitlines() if line]
    event = json.loads(lines[-1])
    assert event["event"] == "server_ready"
    assert event["level"] == "info"
    assert event["service"] == "prompteer-api"
    assert event["version"] == "test-version"
    assert event["env"] == "test"
    assert "request_id" in event
