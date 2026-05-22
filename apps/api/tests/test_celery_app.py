"""Tests for Celery worker logging and runtime configuration."""

from app.tasks.celery_app import celery_app


def test_celery_worker_preserves_structured_logging() -> None:
    assert celery_app.conf.worker_hijack_root_logger is False
    assert celery_app.conf.timezone == "UTC"
