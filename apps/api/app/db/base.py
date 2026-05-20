"""SQLModel metadata import target for Alembic autogeneration."""

from sqlmodel import SQLModel

import app.models  # noqa: F401

__all__ = ["SQLModel"]
