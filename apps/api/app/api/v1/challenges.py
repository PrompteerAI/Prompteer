"""API v1 challenge routes; no sibling challenge API version exists yet."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlmodel import Session, col, select

from app.api.deps import get_current_principal
from app.core.feature_flags import require_feature_enabled
from app.core.ratelimit import GENERAL_RATE_LIMIT, LLM_RATE_LIMIT, limiter
from app.core.security import Principal
from app.core.time import ensure_utc
from app.db.session import get_session
from app.integrations.llm import get_llm_client
from app.models.domain import Challenge, ChallengeTag, Share
from app.schemas.challenge import (
    ChallengeRead,
    ChallengeRunRequest,
    ChallengeRunResponse,
    ChallengeRunShareRead,
)
from app.services.llm_quota import (
    assert_llm_quota_available,
    record_llm_usage,
    resolve_user_for_principal,
)

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.get("")
@limiter.limit(GENERAL_RATE_LIMIT)
async def list_challenges(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    tag: Annotated[ChallengeTag | None, Query()] = None,
) -> list[ChallengeRead]:
    del request, response
    statement = select(Challenge).order_by(col(Challenge.challenge_number))
    if tag is not None:
        statement = statement.where(Challenge.tag == tag)
    return [challenge_to_read(challenge) for challenge in session.exec(statement).all()]


@router.get("/{challenge_id}")
@limiter.limit(GENERAL_RATE_LIMIT)
async def get_challenge(
    request: Request,
    response: Response,
    challenge_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ChallengeRead:
    del request, response
    return challenge_to_read(load_challenge(session, challenge_id))


@router.post("/{challenge_id}/run")
@limiter.limit(LLM_RATE_LIMIT)
async def run_challenge_prompt(
    request: Request,
    response: Response,
    challenge_id: str,
    run_request: ChallengeRunRequest,
    session: Annotated[Session, Depends(get_session)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> ChallengeRunResponse:
    del request, response
    require_feature_enabled("llm")
    challenge = load_challenge(session, challenge_id)
    user = resolve_user_for_principal(session, principal)
    assert_llm_quota_available(session, user)
    llm_client = get_llm_client()
    llm_response = await llm_client.chat_completion(
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
    record_llm_usage(session, user, llm_response["usage"])
    share = create_prompt_share(
        session,
        user_id=user.id,
        challenge_id=challenge.id,
        run=run_request,
    )
    message = llm_response["choices"][0]["message"]
    return ChallengeRunResponse(
        challenge=challenge_to_read(challenge),
        prompt=run_request.prompt,
        provider=llm_client.provider,
        output=str(message["content"]),
        usage=llm_response["usage"],
        raw=llm_response,
        share=share_to_run_read(share) if share is not None else None,
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


def create_prompt_share(
    session: Session,
    *,
    user_id: str,
    challenge_id: str,
    run: ChallengeRunRequest,
) -> Share | None:
    if not run.publish_to_board:
        return None
    share = Share(
        challenge_id=challenge_id,
        user_id=user_id,
        prompt=run.prompt,
        is_public=True,
    )
    session.add(share)
    session.commit()
    session.refresh(share)
    return share


def share_to_run_read(share: Share) -> ChallengeRunShareRead:
    return ChallengeRunShareRead(
        id=share.id,
        is_public=share.is_public,
        created_at=ensure_utc(share.created_at),
    )
