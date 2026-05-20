from datetime import datetime

from pydantic import BaseModel

from app.models.domain import ChallengeLevel, ChallengeTag, PostType


class AuthorRead(BaseModel):
    id: str
    display_name: str
    email: str
    plan: str


class ChallengeSummaryRead(BaseModel):
    id: str
    challenge_number: int
    tag: ChallengeTag
    level: ChallengeLevel
    title: str


class PostRead(BaseModel):
    id: str
    type: PostType
    tag: ChallengeTag
    title: str
    content: str | None
    author: AuthorRead
    challenge: ChallengeSummaryRead | None
    created_at: datetime


class ShareRead(BaseModel):
    id: str
    prompt: str | None
    is_public: bool
    author: AuthorRead
    challenge: ChallengeSummaryRead
    created_at: datetime


class BoardFeedRead(BaseModel):
    posts: list[PostRead]
    shares: list[ShareRead]
