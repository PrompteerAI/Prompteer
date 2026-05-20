from celery import Celery  # type: ignore[import-untyped]

from app.core.config import settings

celery_app = Celery(
    "prompteer",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    timezone="UTC",
    enable_utc=True,
)
