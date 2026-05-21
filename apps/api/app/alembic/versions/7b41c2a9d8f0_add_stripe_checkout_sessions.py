"""add stripe checkout sessions

Revision ID: 7b41c2a9d8f0
Revises: f3a9d2c7e6b1
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "7b41c2a9d8f0"
down_revision: str | None = "f3a9d2c7e6b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("stripe_checkout_sessions"):
        return

    op.create_table(
        "stripe_checkout_sessions",
        sa.Column("provider_session_id", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("plan", sa.String(length=30), nullable=False),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("payment_status", sa.String(length=30), nullable=False),
        sa.Column("amount_total", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column("customer_email", sa.String(length=320), nullable=True),
        sa.Column("client_reference_id", sa.String(length=255), nullable=True),
        sa.Column("session_metadata", sa.JSON(), nullable=False),
        sa.Column("checkout_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("provider_session_id"),
    )
    op.create_index(
        "ix_stripe_checkout_sessions_user_id",
        "stripe_checkout_sessions",
        ["user_id"],
    )
    op.create_index(
        "ix_stripe_checkout_sessions_status",
        "stripe_checkout_sessions",
        ["status"],
    )
    op.create_index(
        "ix_stripe_checkout_sessions_payment_status",
        "stripe_checkout_sessions",
        ["payment_status"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("stripe_checkout_sessions"):
        return

    op.drop_index(
        "ix_stripe_checkout_sessions_payment_status", table_name="stripe_checkout_sessions"
    )
    op.drop_index("ix_stripe_checkout_sessions_status", table_name="stripe_checkout_sessions")
    op.drop_index("ix_stripe_checkout_sessions_user_id", table_name="stripe_checkout_sessions")
    op.drop_table("stripe_checkout_sessions")
