from __future__ import annotations

import asyncio
from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config
from sqlmodel import Session

from app.core.config import settings
from app.db.seed import seed, seed_mock_emails
from app.db.session import engine

logger = structlog.get_logger(__name__)


async def bootstrap_development_state() -> None:
    if settings.is_production or not settings.auto_seed_on_startup:
        logger.info(
            "development_bootstrap_skipped",
            reason="production" if settings.is_production else "disabled",
        )
        return

    for attempt in range(1, settings.dev_bootstrap_retries + 1):
        try:
            await asyncio.to_thread(run_development_bootstrap)
        except Exception as exc:
            if attempt >= settings.dev_bootstrap_retries:
                logger.error("development_bootstrap_failed", attempt=attempt, exc_info=exc)
                raise
            logger.warning(
                "development_bootstrap_retrying",
                attempt=attempt,
                retry_seconds=settings.dev_bootstrap_retry_seconds,
                exc_info=exc,
            )
            await asyncio.sleep(settings.dev_bootstrap_retry_seconds)
        else:
            logger.info("development_bootstrap_completed")
            return


def run_development_bootstrap() -> None:
    command.upgrade(alembic_config(), "head")
    with Session(engine) as session:
        seed(session)
    seed_mock_emails()


def alembic_config() -> Config:
    api_root = Path(__file__).resolve().parents[2]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "app" / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def integration_modes() -> dict[str, str]:
    return {
        "llm": "real" if settings.openai_api_key or settings.anthropic_api_key else "mock",
        "google_oauth": "real"
        if settings.google_client_id and settings.google_client_secret
        else "mock",
        "stripe": "real" if settings.stripe_secret_key else "mock",
        "email": "real" if settings.sendgrid_api_key else "mock",
    }
