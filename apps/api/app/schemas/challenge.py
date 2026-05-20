from pydantic import BaseModel, Field

from app.models.domain import ChallengeLevel, ChallengeTag


class ChallengeRead(BaseModel):
    id: str
    challenge_number: int
    tag: ChallengeTag
    level: ChallengeLevel
    title: str
    content: str | None


class ChallengeRunRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=4000)


class ChallengeRunResponse(BaseModel):
    challenge: ChallengeRead
    prompt: str
    provider: str
    output: str
    usage: dict[str, int]
    raw: dict[str, object]
