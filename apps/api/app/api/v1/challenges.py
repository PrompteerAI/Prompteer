from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session, col, select

from app.core.ratelimit import LLM_RATE_LIMIT, limiter
from app.db.session import get_session
from app.integrations.llm import get_llm_client
from app.models.domain import Challenge, ChallengeTag
from app.schemas.challenge import ChallengeRead, ChallengeRunRequest, ChallengeRunResponse

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("")
async def list_challenges(
    session: Annotated[Session, Depends(get_session)],
    tag: Annotated[ChallengeTag | None, Query()] = None,
) -> list[ChallengeRead]:
    statement = select(Challenge).order_by(col(Challenge.challenge_number))
    if tag is not None:
        statement = statement.where(Challenge.tag == tag)
    return [challenge_to_read(challenge) for challenge in session.exec(statement).all()]


@router.get("/{challenge_id}")
async def get_challenge(
    challenge_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ChallengeRead:
    return challenge_to_read(load_challenge(session, challenge_id))


@router.post("/{challenge_id}/run")
@limiter.limit(LLM_RATE_LIMIT)
async def run_challenge_prompt(
    request: Request,
    challenge_id: str,
    run_request: ChallengeRunRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ChallengeRunResponse:
    del request
    challenge = load_challenge(session, challenge_id)
    llm_client = get_llm_client()
    response = await llm_client.chat_completion(
        {
            "model": "mock-gpt-4.1-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are evaluating a Prompteer challenge submission. "
                        "Respond with concise feedback and a stronger prompt."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Challenge: {challenge.title}\n"
                        f"Instructions: {challenge.content or 'No extra instructions.'}\n"
                        f"Submitted prompt: {run_request.prompt}"
                    ),
                },
            ],
        }
    )
    message = response["choices"][0]["message"]
    return ChallengeRunResponse(
        challenge=challenge_to_read(challenge),
        prompt=run_request.prompt,
        provider=llm_client.provider,
        output=str(message["content"]),
        usage=response["usage"],
        raw=response,
    )


def load_challenge(session: Session, challenge_id: str) -> Challenge:
    challenge = session.get(Challenge, challenge_id)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found.",
        )
    return challenge


def challenge_to_read(challenge: Challenge) -> ChallengeRead:
    return ChallengeRead(
        id=challenge.id,
        challenge_number=challenge.challenge_number,
        tag=challenge.tag,
        level=challenge.level,
        title=challenge.title,
        content=challenge.content,
    )
