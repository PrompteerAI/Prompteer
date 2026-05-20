"""initial domain schema

Revision ID: bd1c81512fff
Revises:
Create Date: 2026-05-20 17:44:43.168603
"""

from collections.abc import Sequence

from alembic import op
from sqlmodel import SQLModel

import app.models  # noqa: F401

revision: str = "bd1c81512fff"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    SQLModel.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    SQLModel.metadata.drop_all(bind=op.get_bind())
