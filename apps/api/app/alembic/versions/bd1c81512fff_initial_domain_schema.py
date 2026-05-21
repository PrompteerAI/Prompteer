"""initial domain schema

Revision ID: bd1c81512fff
Revises:
Create Date: 2026-05-20 17:44:43.168603
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "bd1c81512fff"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def challenge_tag_enum() -> sa.Enum:
    return sa.Enum("ps", "img", "video", name="challengetag")


def challenge_level_enum() -> sa.Enum:
    return sa.Enum("easy", "medium", "hard", name="challengelevel")


def post_type_enum() -> sa.Enum:
    return sa.Enum("question", "share", name="posttype")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("auth_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("plan", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_auth_subject", "users", ["auth_subject"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "challenges",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("tag", challenge_tag_enum(), nullable=False),
        sa.Column("level", challenge_level_enum(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("content", sa.String(), nullable=True),
        sa.Column("challenge_number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_challenges_challenge_number", "challenges", ["challenge_number"], unique=True
    )
    op.create_index("ix_challenges_level", "challenges", ["level"])
    op.create_index("ix_challenges_owner_id", "challenges", ["owner_id"])
    op.create_index("ix_challenges_tag", "challenges", ["tag"])

    op.create_table(
        "profiles",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("introduction", sa.String(length=500), nullable=True),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "img_challenges",
        sa.Column("challenge_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.PrimaryKeyConstraint("challenge_id"),
    )

    op.create_table(
        "posts",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("challenge_id", sa.String(), nullable=True),
        sa.Column("type", post_type_enum(), nullable=False),
        sa.Column("tag", challenge_tag_enum(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("content", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_posts_challenge_id", "posts", ["challenge_id"])
    op.create_index("ix_posts_tag", "posts", ["tag"])
    op.create_index("ix_posts_type", "posts", ["type"])
    op.create_index("ix_posts_user_id", "posts", ["user_id"])

    op.create_table(
        "ps_challenges",
        sa.Column("challenge_id", sa.String(), nullable=False),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.PrimaryKeyConstraint("challenge_id"),
    )

    op.create_table(
        "shares",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("challenge_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("prompt", sa.String(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shares_challenge_id", "shares", ["challenge_id"])
    op.create_index("ix_shares_is_public", "shares", ["is_public"])
    op.create_index("ix_shares_user_id", "shares", ["user_id"])

    op.create_table(
        "video_challenges",
        sa.Column("challenge_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"]),
        sa.PrimaryKeyConstraint("challenge_id"),
    )

    op.create_table(
        "attachments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("post_id", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_attachments_post_id", "attachments", ["post_id"])

    op.create_table(
        "comments",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("post_id", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comments_post_id", "comments", ["post_id"])
    op.create_index("ix_comments_user_id", "comments", ["user_id"])

    op.create_table(
        "img_references",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("challenge_id", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["img_challenges.challenge_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_img_references_challenge_id", "img_references", ["challenge_id"])

    op.create_table(
        "img_shares",
        sa.Column("share_id", sa.String(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["share_id"], ["shares.id"]),
        sa.PrimaryKeyConstraint("share_id"),
    )

    op.create_table(
        "ps_shares",
        sa.Column("share_id", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("runtime_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["share_id"], ["shares.id"]),
        sa.PrimaryKeyConstraint("share_id"),
    )
    op.create_index("ix_ps_shares_is_correct", "ps_shares", ["is_correct"])

    op.create_table(
        "ps_testcases",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("challenge_id", sa.String(), nullable=False),
        sa.Column("input", sa.String(), nullable=True),
        sa.Column("output", sa.String(), nullable=True),
        sa.Column("time_limit_seconds", sa.Float(), nullable=False),
        sa.Column("memory_limit_mb", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["ps_challenges.challenge_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ps_testcases_challenge_id", "ps_testcases", ["challenge_id"])

    op.create_table(
        "user_likes_posts",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("post_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "post_id"),
    )

    op.create_table(
        "user_likes_shares",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("share_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["share_id"], ["shares.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "share_id"),
    )

    op.create_table(
        "video_references",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("challenge_id", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["video_challenges.challenge_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_video_references_challenge_id", "video_references", ["challenge_id"])

    op.create_table(
        "video_shares",
        sa.Column("share_id", sa.String(), nullable=False),
        sa.Column("video_url", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["share_id"], ["shares.id"]),
        sa.PrimaryKeyConstraint("share_id"),
    )

    op.create_table(
        "user_likes_comments",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("comment_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["comments.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id", "comment_id"),
    )


def downgrade() -> None:
    for table_name in (
        "user_likes_comments",
        "video_shares",
        "video_references",
        "user_likes_shares",
        "user_likes_posts",
        "ps_testcases",
        "ps_shares",
        "img_shares",
        "img_references",
        "comments",
        "attachments",
        "video_challenges",
        "shares",
        "ps_challenges",
        "posts",
        "img_challenges",
        "profiles",
        "challenges",
        "users",
    ):
        op.drop_table(table_name)
    drop_postgresql_enum_types()


def drop_postgresql_enum_types() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute(sa.text("DROP TYPE IF EXISTS posttype"))
    op.execute(sa.text("DROP TYPE IF EXISTS challengelevel"))
    op.execute(sa.text("DROP TYPE IF EXISTS challengetag"))
