"""enforce one share per user and challenge

Revision ID: a4d9c2f81b6a
Revises: 7b41c2a9d8f0
Create Date: 2026-05-21 18:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a4d9c2f81b6a"
down_revision: str | None = "7b41c2a9d8f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM shares
            WHERE id IN (
              SELECT id
              FROM (
                SELECT
                  id,
                  row_number() OVER (
                    PARTITION BY user_id, challenge_id
                    ORDER BY updated_at DESC, created_at DESC, id DESC
                  ) AS duplicate_rank
                FROM shares
              ) ranked_shares
              WHERE duplicate_rank > 1
            )
            """
        )
    )
    op.create_index(
        "uq_shares_user_challenge",
        "shares",
        ["user_id", "challenge_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_shares_user_challenge", table_name="shares")
