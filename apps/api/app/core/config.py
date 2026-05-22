"""Typed application settings loaded from environment variables and .env files."""

from functools import lru_cache
from typing import Literal, TypedDict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

RealMockIntegrationMode = Literal["mock", "real"]
GoogleOAuthIntegrationMode = Literal["mock", "partial", "real"]


class IntegrationModes(TypedDict):
    llm: RealMockIntegrationMode
    google_oauth: GoogleOAuthIntegrationMode
    stripe: RealMockIntegrationMode
    email: RealMockIntegrationMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development", alias="ENV")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    app_url: str = Field(default="http://localhost:3000", alias="APP_URL")
    database_url: str = Field(
        default="postgresql+psycopg://prompteer:prompteer@localhost:55432/prompteer",
        alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=5, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: float = Field(default=30.0, alias="DATABASE_POOL_TIMEOUT")
    redis_url: str = Field(default="redis://localhost:56379/0", alias="REDIS_URL")
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_storage_url: str = Field(
        default="redis://localhost:56379/0",
        alias="RATE_LIMIT_STORAGE_URL",
    )
    rate_limit_strategy: str = Field(default="moving-window", alias="RATE_LIMIT_STRATEGY")
    rate_limit_key_prefix: str = Field(default="prompteer", alias="RATE_LIMIT_KEY_PREFIX")
    rate_limit_headers_enabled: bool = Field(default=True, alias="RATE_LIMIT_HEADERS_ENABLED")
    rate_limit_trusted_proxy_cidrs: str = Field(
        default="127.0.0.1/32,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
        alias="RATE_LIMIT_TRUSTED_PROXY_CIDRS",
    )
    general_rate_limit: str = Field(default="60/minute", alias="GENERAL_RATE_LIMIT")
    auth_attempt_rate_limit: str = Field(default="120/minute", alias="AUTH_ATTEMPT_RATE_LIMIT")
    llm_rate_limit: str = Field(default="10/minute;200/hour", alias="LLM_RATE_LIMIT")
    payments_rate_limit: str = Field(default="5/minute", alias="PAYMENTS_RATE_LIMIT")
    stripe_webhook_rate_limit: str = Field(
        default="120/minute",
        alias="STRIPE_WEBHOOK_RATE_LIMIT",
    )
    email_rate_limit: str = Field(default="5/minute;20/day", alias="EMAIL_RATE_LIMIT")
    llm_free_daily_token_cap: int = Field(default=50_000, alias="LLM_FREE_DAILY_TOKEN_CAP")
    llm_paid_daily_token_cap: int = Field(default=500_000, alias="LLM_PAID_DAILY_TOKEN_CAP")
    auto_seed_on_startup: bool = Field(default=True, alias="AUTO_SEED_ON_STARTUP")
    dev_bootstrap_retries: int = Field(default=30, alias="DEV_BOOTSTRAP_RETRIES")
    dev_bootstrap_retry_seconds: float = Field(default=1.0, alias="DEV_BOOTSTRAP_RETRY_SECONDS")
    auth_allow_seed_login: bool = Field(default=True, alias="AUTH_ALLOW_SEED_LOGIN")
    enable_dev_routes: bool = Field(default=True, alias="ENABLE_DEV_ROUTES")
    auth_jwks_url: str = Field(
        default="http://localhost:3000/api/auth/jwks",
        alias="AUTH_JWKS_URL",
    )
    auth_jwt_issuer: str = Field(default="http://localhost:3000", alias="AUTH_JWT_ISSUER")
    auth_jwt_audience: str = Field(default="prompteer-api", alias="AUTH_JWT_AUDIENCE")
    log_json: bool = Field(default=False, alias="LOG_JSON")
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    api_gunicorn_timeout: int = Field(default=30, alias="API_GUNICORN_TIMEOUT")
    api_gunicorn_graceful_timeout: int = Field(
        default=30,
        alias="API_GUNICORN_GRACEFUL_TIMEOUT",
    )
    api_gunicorn_keepalive: int = Field(default=2, alias="API_GUNICORN_KEEPALIVE")

    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    auth_mock_google_issuer: str = Field(
        default="http://localhost:8000",
        alias="AUTH_MOCK_GOOGLE_ISSUER",
    )
    auth_mock_google_server_base_url: str = Field(
        default="",
        alias="AUTH_MOCK_GOOGLE_SERVER_BASE_URL",
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_chat_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_CHAT_MODEL")
    openai_max_completion_tokens: int = Field(default=512, alias="OPENAI_MAX_COMPLETION_TOKENS")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com/v1",
        alias="ANTHROPIC_BASE_URL",
    )
    anthropic_model: str = Field(default="claude-sonnet-4-20250514", alias="ANTHROPIC_MODEL")
    anthropic_version: str = Field(default="2023-06-01", alias="ANTHROPIC_VERSION")
    stripe_secret_key: str = Field(default="", alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="", alias="STRIPE_WEBHOOK_SECRET")
    sendgrid_api_key: str = Field(default="", alias="SENDGRID_API_KEY")
    sendgrid_from_email: str = Field(default="no-reply@prompteer.dev", alias="SENDGRID_FROM_EMAIL")
    mock_mailbox_dir: str = Field(default="", alias="MOCK_MAILBOX_DIR")
    feature_llm_enabled: bool = Field(default=True, alias="FEATURE_LLM_ENABLED")
    feature_payments_enabled: bool = Field(default=True, alias="FEATURE_PAYMENTS_ENABLED")
    feature_email_enabled: bool = Field(default=True, alias="FEATURE_EMAIL_ENABLED")

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def credential_is_set(value: str) -> bool:
    return bool(value.strip())


def credential_value(value: str) -> str:
    return value.strip()


def google_oauth_integration_mode(
    config: Settings | None = None,
) -> GoogleOAuthIntegrationMode:
    active_settings = config or settings
    has_client_id = credential_is_set(active_settings.google_client_id)
    has_client_secret = credential_is_set(active_settings.google_client_secret)
    if has_client_id != has_client_secret:
        return "partial"
    if has_client_id and has_client_secret:
        return "real"
    return "mock"


def integration_modes(config: Settings | None = None) -> IntegrationModes:
    active_settings = config or settings
    return {
        "llm": "real"
        if credential_is_set(active_settings.openai_api_key)
        or credential_is_set(active_settings.anthropic_api_key)
        else "mock",
        "google_oauth": google_oauth_integration_mode(active_settings),
        "stripe": "real" if credential_is_set(active_settings.stripe_secret_key) else "mock",
        "email": "real" if credential_is_set(active_settings.sendgrid_api_key) else "mock",
    }
