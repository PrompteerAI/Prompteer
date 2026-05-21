"""make domain timestamps timezone aware

Revision ID: c9b2a71e4f6d
Revises: 8d2f4a9c1b7e
Create Date: 2026-05-21 16:30:00.000000

The initial SQLModel-created schema stored TimestampMixin columns as
`timestamp without time zone`. Prompteer stores all domain datetimes in UTC, so
these columns must be `timestamp with time zone` in PostgreSQL.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9b2a71e4f6d"
down_revision: str | None = "8d2f4a9c1b7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TIMESTAMP_TABLES = ("users", "challenges", "shares", "posts", "comments")
TIMESTAMP_COLUMNS = ("created_at", "updated_at")


def upgrade() -> None:
    alter_timestamp_columns(timezone=True)


def downgrade() -> None:
    alter_timestamp_columns(timezone=False)


def alter_timestamp_columns(*, timezone: bool) -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table_name in TIMESTAMP_TABLES:
        for column_name in TIMESTAMP_COLUMNS:
            op.alter_column(
                table_name,
                column_name,
                existing_type=sa.DateTime(timezone=not timezone),
                type_=sa.DateTime(timezone=timezone),
                existing_nullable=False,
                postgresql_using=f"{column_name} AT TIME ZONE 'UTC'",
            )
