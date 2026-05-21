"""Database engine and session dependency for API routes and seed scripts."""

from collections.abc import Generator
from typing import Any

from sqlmodel import Session, create_engine

from app.core.config import settings


def database_engine_kwargs() -> dict[str, Any]:
    return {
        "pool_pre_ping": True,
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "pool_timeout": settings.database_pool_timeout,
    }


engine = create_engine(settings.database_url, **database_engine_kwargs())


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
