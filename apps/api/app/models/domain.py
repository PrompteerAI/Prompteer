"""SQLModel domain tables for users, challenges, shares, posts, and usage."""

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field, SQLModel

UTCDateTime = cast(type[Any], DateTime(timezone=True))


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


class ChallengeTag(StrEnum):
    ps = "ps"
    img = "img"
    video = "video"


class ChallengeLevel(StrEnum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class PostType(StrEnum):
    question = "question"
    share = "share"


class TimestampMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=UTCDateTime,
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=UTCDateTime,
        nullable=False,
    )


class User(TimestampMixin, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    auth_subject: str = Field(index=True, unique=True, max_length=255)
    email: str = Field(index=True, unique=True, max_length=320)
    display_name: str = Field(max_length=100)
    role: str = Field(default="user", max_length=30)
    plan: str = Field(default="free", max_length=30)
    is_active: bool = Field(default=True)


class LLMUsageDay(SQLModel, table=True):
    __tablename__ = "llm_usage_days"

    user_id: str = Field(foreign_key="users.id", primary_key=True)
    usage_date: date = Field(primary_key=True, index=True)
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    request_count: int = Field(default=0, ge=0)
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class StripeWebhookEvent(SQLModel, table=True):
    __tablename__ = "stripe_webhook_events"

    event_id: str = Field(primary_key=True, max_length=255)
    event_type: str = Field(index=True, max_length=255)
    processed: bool = Field(default=False)
    customer_email: str | None = Field(default=None, max_length=320)
    user_id: str | None = Field(default=None, foreign_key="users.id", index=True)
    received_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    user_id: str = Field(foreign_key="users.id", primary_key=True)
    introduction: str | None = Field(default=None, max_length=500)
    interests: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Challenge(TimestampMixin, table=True):
    __tablename__ = "challenges"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    owner_id: str = Field(foreign_key="users.id", index=True)
    tag: ChallengeTag = Field(index=True)
    level: ChallengeLevel = Field(index=True)
    title: str = Field(max_length=160)
    content: str | None = Field(default=None)
    challenge_number: int = Field(index=True, unique=True)


class PSChallenge(SQLModel, table=True):
    __tablename__ = "ps_challenges"

    challenge_id: str = Field(foreign_key="challenges.id", primary_key=True)
    language: str = Field(default="python", max_length=50)


class PSTestcase(SQLModel, table=True):
    __tablename__ = "ps_testcases"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    challenge_id: str = Field(foreign_key="ps_challenges.challenge_id", index=True)
    input: str | None = None
    output: str | None = None
    time_limit_seconds: float = Field(default=2.0)
    memory_limit_mb: int = Field(default=128)


class ImgChallenge(SQLModel, table=True):
    __tablename__ = "img_challenges"

    challenge_id: str = Field(foreign_key="challenges.id", primary_key=True)


class ImgReference(SQLModel, table=True):
    __tablename__ = "img_references"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    challenge_id: str = Field(foreign_key="img_challenges.challenge_id", index=True)
    file_path: str = Field(max_length=500)
    file_type: str = Field(max_length=100)


class VideoChallenge(SQLModel, table=True):
    __tablename__ = "video_challenges"

    challenge_id: str = Field(foreign_key="challenges.id", primary_key=True)


class VideoReference(SQLModel, table=True):
    __tablename__ = "video_references"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    challenge_id: str = Field(foreign_key="video_challenges.challenge_id", index=True)
    file_path: str = Field(max_length=500)
    file_type: str = Field(max_length=100)


class Share(TimestampMixin, table=True):
    __tablename__ = "shares"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    challenge_id: str = Field(foreign_key="challenges.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    prompt: str | None = None
    is_public: bool = Field(default=True, index=True)


class PSShare(SQLModel, table=True):
    __tablename__ = "ps_shares"

    share_id: str = Field(foreign_key="shares.id", primary_key=True)
    code: str | None = None
    is_correct: bool = Field(default=False, index=True)
    runtime_ms: int | None = None
    memory_kb: int | None = None


class ImgShare(SQLModel, table=True):
    __tablename__ = "img_shares"

    share_id: str = Field(foreign_key="shares.id", primary_key=True)
    image_url: str = Field(max_length=500)


class VideoShare(SQLModel, table=True):
    __tablename__ = "video_shares"

    share_id: str = Field(foreign_key="shares.id", primary_key=True)
    video_url: str = Field(max_length=500)


class Post(TimestampMixin, table=True):
    __tablename__ = "posts"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    challenge_id: str | None = Field(default=None, foreign_key="challenges.id", index=True)
    type: PostType = Field(index=True)
    tag: ChallengeTag = Field(index=True)
    title: str = Field(max_length=160)
    content: str | None = None


class Attachment(SQLModel, table=True):
    __tablename__ = "attachments"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    post_id: str = Field(foreign_key="posts.id", index=True)
    file_path: str = Field(max_length=500)
    file_type: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Comment(TimestampMixin, table=True):
    __tablename__ = "comments"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    post_id: str = Field(foreign_key="posts.id", index=True)
    content: str


class UserLikesShare(SQLModel, table=True):
    __tablename__ = "user_likes_shares"

    user_id: str = Field(foreign_key="users.id", primary_key=True)
    share_id: str = Field(foreign_key="shares.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class UserLikesPost(SQLModel, table=True):
    __tablename__ = "user_likes_posts"

    user_id: str = Field(foreign_key="users.id", primary_key=True)
    post_id: str = Field(foreign_key="posts.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class UserLikesComment(SQLModel, table=True):
    __tablename__ = "user_likes_comments"

    user_id: str = Field(foreign_key="users.id", primary_key=True)
    comment_id: str = Field(foreign_key="comments.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
