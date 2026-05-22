"""Celery worker application configured for Redis-backed background jobs."""

from celery import Celery  # type: ignore[import-untyped]

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.observability import init_observability

configure_logging()
init_observability()

celery_app = Celery(
    "prompteer",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_hijack_root_logger=False,
    timezone="UTC",
    enable_utc=True,
)
