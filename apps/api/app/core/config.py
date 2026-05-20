from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="development", alias="ENV")
    app_url: str = Field(default="http://localhost:3000", alias="APP_URL")
    database_url: str = Field(
        default="postgresql+psycopg://prompteer:prompteer@localhost:5432/prompteer",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_storage_url: str = Field(default="memory://", alias="RATE_LIMIT_STORAGE_URL")
    rate_limit_strategy: str = Field(default="moving-window", alias="RATE_LIMIT_STRATEGY")
    rate_limit_key_prefix: str = Field(default="prompteer", alias="RATE_LIMIT_KEY_PREFIX")
    rate_limit_headers_enabled: bool = Field(default=True, alias="RATE_LIMIT_HEADERS_ENABLED")
    rate_limit_in_memory_fallback_enabled: bool = Field(
        default=True,
        alias="RATE_LIMIT_IN_MEMORY_FALLBACK_ENABLED",
    )
    llm_rate_limit: str = Field(default="10/minute", alias="LLM_RATE_LIMIT")
    payments_rate_limit: str = Field(default="20/minute", alias="PAYMENTS_RATE_LIMIT")
    email_rate_limit: str = Field(default="5/minute", alias="EMAIL_RATE_LIMIT")
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

    google_client_id: str = Field(default="", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", alias="GOOGLE_CLIENT_SECRET")
    auth_mock_google_issuer: str = Field(
        default="http://localhost:8000",
        alias="AUTH_MOCK_GOOGLE_ISSUER",
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_base_url: str = Field(
        default="https://api.anthropic.com/v1",
        alias="ANTHROPIC_BASE_URL",
    )
    anthropic_version: str = Field(default="2023-06-01", alias="ANTHROPIC_VERSION")
    stripe_secret_key: str = Field(default="", alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="", alias="STRIPE_WEBHOOK_SECRET")
    sendgrid_api_key: str = Field(default="", alias="SENDGRID_API_KEY")
    sendgrid_from_email: str = Field(default="no-reply@prompteer.dev", alias="SENDGRID_FROM_EMAIL")
    feature_llm_enabled: bool = Field(default=True, alias="FEATURE_LLM_ENABLED")
    feature_payments_enabled: bool = Field(default=True, alias="FEATURE_PAYMENTS_ENABLED")
    feature_email_enabled: bool = Field(default=True, alias="FEATURE_EMAIL_ENABLED")

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
