"""SQLModel metadata import target for Alembic autogeneration."""

from sqlmodel import SQLModel

# Import model modules so Alembic autogeneration sees every SQLModel table.
import app.models  # noqa: F401

__all__ = ["SQLModel"]
