"""Tests for SQLModel metadata and timezone-aware domain defaults."""

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import SQLModel

# Import model modules so SQLModel metadata is populated before assertions.
import app.models  # noqa: F401
from app.models.domain import Challenge, ChallengeLevel, ChallengeTag, User, utc_now


def test_domain_tables_are_registered() -> None:
    expected = {
        "attachments",
        "challenges",
        "comments",
        "img_challenges",
        "img_references",
        "img_shares",
        "llm_usage_days",
        "posts",
        "profiles",
        "ps_challenges",
        "ps_shares",
        "ps_testcases",
        "shares",
        "stripe_checkout_sessions",
        "stripe_webhook_events",
        "user_likes_comments",
        "user_likes_posts",
        "user_likes_shares",
        "users",
        "video_challenges",
        "video_references",
        "video_shares",
    }

    assert expected.issubset(SQLModel.metadata.tables.keys())


def test_domain_models_use_utc_timestamps() -> None:
    user = User(auth_subject="google-oauth2|123", email="free@prompteer.dev", display_name="Free")
    challenge = Challenge(
        owner_id=user.id,
        tag=ChallengeTag.ps,
        level=ChallengeLevel.easy,
        title="FizzBuzz prompt",
        challenge_number=1,
    )

    assert user.created_at.tzinfo is not None
    assert challenge.created_at.tzinfo is not None
    assert utc_now().tzinfo is not None


def test_domain_timestamp_columns_are_timezone_aware() -> None:
    timestamp_columns = {
        "users": ("created_at", "updated_at"),
        "challenges": ("created_at", "updated_at"),
        "shares": ("created_at", "updated_at"),
        "posts": ("created_at", "updated_at"),
        "comments": ("created_at", "updated_at"),
    }

    for table_name, column_names in timestamp_columns.items():
        table = SQLModel.metadata.tables[table_name]
        for column_name in column_names:
            column_type = table.columns[column_name].type
            assert isinstance(column_type, DateTime)
            assert column_type.timezone is True


def test_share_model_enforces_one_share_per_user_challenge() -> None:
    table = SQLModel.metadata.tables["shares"]
    unique_constraints = [
        constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
    ]

    assert any(
        constraint.name == "uq_shares_user_challenge"
        and {column.name for column in constraint.columns} == {"user_id", "challenge_id"}
        for constraint in unique_constraints
    )
