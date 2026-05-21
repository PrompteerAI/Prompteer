"""Shared test helpers for resetting infrastructure-backed runtime components."""

from app.core.ratelimit import limiter


def reset_limiter_storage() -> None:
    """Reset SlowAPI Redis storage between tests."""
    limiter.reset()
    limiter._storage_dead = False
