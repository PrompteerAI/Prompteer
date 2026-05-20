"""Shared test helpers for resetting infrastructure-backed runtime components."""

from typing import Any

from redis.exceptions import RedisError

from app.core.ratelimit import limiter


def reset_limiter_storage() -> None:
    """Reset SlowAPI storage while tolerating Redis being absent in local unit tests."""
    try:
        limiter.reset()
        limiter._storage_dead = False
    except RedisError:
        limiter._storage_dead = True
        fallback_storage: Any = getattr(limiter, "_fallback_storage", None)
        if fallback_storage is not None:
            fallback_storage.reset()
