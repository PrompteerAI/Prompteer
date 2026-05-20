"""Alembic helpers used by startup health checks and development bootstrap."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Engine

from app.core.config import settings
from app.db.session import engine as default_engine


@dataclass(frozen=True)
class MigrationState:
    status: Literal["ok", "fail"]
    current: str | None
    head: str | None
    detail: str | None = None


def alembic_config() -> Config:
    api_root = Path(__file__).resolve().parents[2]
    config = Config(str(api_root / "alembic.ini"))
    config.set_main_option("script_location", str(api_root / "app" / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def migration_state(engine: Engine = default_engine) -> MigrationState:
    try:
        config = alembic_config()
        head = ScriptDirectory.from_config(config).get_current_head()
        with engine.connect() as connection:
            current = MigrationContext.configure(connection).get_current_revision()
    except Exception as exc:
        return MigrationState(status="fail", current=None, head=None, detail=str(exc))

    if current != head:
        return MigrationState(
            status="fail",
            current=current,
            head=head,
            detail="database revision does not match alembic head",
        )
    return MigrationState(status="ok", current=current, head=head)
