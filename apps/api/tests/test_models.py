from sqlmodel import SQLModel

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
