"""SQLModel metadata import target for Alembic autogeneration."""

from sqlmodel import SQLModel

# Import model modules so Alembic autogeneration sees every SQLModel table.
import app.models  # noqa: F401  # Populate SQLModel metadata for Alembic autogeneration.

__all__ = ["SQLModel"]
