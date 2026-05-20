"""add llm usage days

Revision ID: 8d2f4a9c1b7e
Revises: bd1c81512fff
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "8d2f4a9c1b7e"
down_revision: str | None = "bd1c81512fff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("llm_usage_days"):
        return

    op.create_table(
        "llm_usage_days",
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("usage_date", sa.Date(), primary_key=True, nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("request_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_llm_usage_days_usage_date",
        "llm_usage_days",
        ["usage_date"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("llm_usage_days"):
        return

    op.drop_index("ix_llm_usage_days_usage_date", table_name="llm_usage_days")
    op.drop_table("llm_usage_days")
