# Pydantic schemas for API v1 challenge reads and prompt run responses.
# These models define the public OpenAPI contract consumed by the web app.

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.models.domain import ChallengeLevel, ChallengeTag


class ImgChallengeReferenceRead(BaseModel):
    kind: Literal["img"]
    id: str
    file_path: str
    file_type: str


class VideoChallengeReferenceRead(BaseModel):
    kind: Literal["video"]
    id: str
    file_path: str
    file_type: str


ChallengeReferenceRead = Annotated[
    ImgChallengeReferenceRead | VideoChallengeReferenceRead,
    Field(discriminator="kind"),
]


class ChallengeRead(BaseModel):
    id: str
    challenge_number: int
    tag: ChallengeTag
    level: ChallengeLevel
    title: str
    content: str | None
    references: list[ChallengeReferenceRead]


class ChallengeRunRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=4000)
    publish_to_board: bool = True


class ChallengeRunShareRead(BaseModel):
    id: str
    is_public: bool
    created_at: datetime


class ChallengeRunResponse(BaseModel):
    challenge: ChallengeRead
    prompt: str
    provider: str
    output: str
    usage: dict[str, int]
    share: ChallengeRunShareRead | None
