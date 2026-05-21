"""Focused tests for runtime configuration helpers."""

import pytest

from app.core.config import integration_modes, settings
from app.db import session as db_session


@pytest.mark.parametrize(
    ("google_client_id", "google_client_secret"),
    [("google-client", ""), ("", "google-secret")],
)
def test_integration_modes_report_partial_google_credentials(
    monkeypatch: pytest.MonkeyPatch,
    google_client_id: str,
    google_client_secret: str,
) -> None:
    monkeypatch.setattr(settings, "google_client_id", google_client_id)
    monkeypatch.setattr(settings, "google_client_secret", google_client_secret)
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    monkeypatch.setattr(settings, "stripe_secret_key", "")
    monkeypatch.setattr(settings, "sendgrid_api_key", "")

    assert integration_modes()["google_oauth"] == "partial"


def test_database_engine_kwargs_reflect_pool_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "database_pool_size", 7)
    monkeypatch.setattr(settings, "database_max_overflow", 11)
    monkeypatch.setattr(settings, "database_pool_timeout", 4.5)

    assert db_session.database_engine_kwargs() == {
        "pool_pre_ping": True,
        "pool_size": 7,
        "max_overflow": 11,
        "pool_timeout": 4.5,
    }
