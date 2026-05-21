"""Development startup bootstrap for migrations, seed data, and mock mailbox files."""

from __future__ import annotations

import asyncio

import structlog
from alembic import command
from sqlmodel import Session

from app.core.config import integration_modes as configured_integration_modes
from app.core.config import settings
from app.core.migrations import alembic_config
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


def main() -> None:
    asyncio.run(bootstrap_development_state())


def integration_modes() -> dict[str, str]:
    modes = configured_integration_modes()
    return {
        "llm": modes["llm"],
        "google_oauth": modes["google_oauth"],
        "stripe": modes["stripe"],
        "email": modes["email"],
    }


if __name__ == "__main__":
    main()
