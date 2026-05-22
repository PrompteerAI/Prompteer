"""Focused tests for runtime configuration helpers."""

from typing import Any, cast

import pytest

from app.core.config import Settings, integration_modes, settings
from app.db import session as db_session


def valid_production_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "ENV": "production",
        "DATABASE_URL": "postgresql+psycopg://prompteer:strong-secret@db:5432/prompteer",
        "GOOGLE_CLIENT_ID": "google-client",
        "GOOGLE_CLIENT_SECRET": "google-secret",
        "OPENAI_API_KEY": "sk-openai",
        "STRIPE_SECRET_KEY": "sk_live_stripe",
        "STRIPE_WEBHOOK_SECRET": "whsec_live",
        "SENDGRID_API_KEY": "SG.live",
        "AUTH_ALLOW_SEED_LOGIN": False,
        "ENABLE_DEV_ROUTES": False,
        "AUTO_SEED_ON_STARTUP": False,
    }
    for key, value in overrides.items():
        if value is None:
            values.pop(key, None)
        else:
            values[key] = value
    return Settings(_env_file=None, **cast(dict[str, Any], values))


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


def test_development_settings_default_dev_only_flags_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTH_ALLOW_SEED_LOGIN", raising=False)
    monkeypatch.delenv("ENABLE_DEV_ROUTES", raising=False)
    monkeypatch.delenv("AUTO_SEED_ON_STARTUP", raising=False)

    config = Settings(_env_file=None, ENV="development")

    assert config.auth_allow_seed_login is True
    assert config.enable_dev_routes is True
    assert config.auto_seed_on_startup is True


def test_production_settings_accept_real_secrets() -> None:
    config = valid_production_settings()

    assert config.is_production is True
    assert config.auth_allow_seed_login is False
    assert config.enable_dev_routes is False
    assert config.auto_seed_on_startup is False
    assert integration_modes(config) == {
        "llm": "real",
        "google_oauth": "real",
        "stripe": "real",
        "email": "real",
    }


def test_production_settings_default_dev_only_flags_are_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AUTH_ALLOW_SEED_LOGIN", raising=False)
    monkeypatch.delenv("ENABLE_DEV_ROUTES", raising=False)
    monkeypatch.delenv("AUTO_SEED_ON_STARTUP", raising=False)

    config = valid_production_settings(
        AUTH_ALLOW_SEED_LOGIN=None,
        ENABLE_DEV_ROUTES=None,
        AUTO_SEED_ON_STARTUP=None,
    )

    assert config.auth_allow_seed_login is False
    assert config.enable_dev_routes is False
    assert config.auto_seed_on_startup is False


def test_production_settings_reject_mock_and_dev_defaults() -> None:
    with pytest.raises(ValueError) as error:
        valid_production_settings(
            DATABASE_URL="postgresql+psycopg://prompteer:prompteer@postgres:5432/prompteer",
            GOOGLE_CLIENT_ID="",
            GOOGLE_CLIENT_SECRET="",
            OPENAI_API_KEY="",
            STRIPE_SECRET_KEY="",
            STRIPE_WEBHOOK_SECRET="",
            SENDGRID_API_KEY="",
            AUTH_ALLOW_SEED_LOGIN=True,
            ENABLE_DEV_ROUTES=True,
            AUTO_SEED_ON_STARTUP=True,
        )

    message = str(error.value)
    assert "DATABASE_URL must not use the default development database secret" in message
    assert "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required" in message
    assert "OPENAI_API_KEY or ANTHROPIC_API_KEY is required" in message
    assert "STRIPE_SECRET_KEY is required" in message
    assert "STRIPE_WEBHOOK_SECRET is required" in message
    assert "SENDGRID_API_KEY is required" in message
    assert "AUTH_ALLOW_SEED_LOGIN must be false" in message
    assert "ENABLE_DEV_ROUTES must be false" in message
    assert "AUTO_SEED_ON_STARTUP must be false" in message
