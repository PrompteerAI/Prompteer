"""API v1 challenge routes; no sibling challenge API version exists yet."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlmodel import Session

from app.api.deps import get_current_principal
from app.core.ratelimit import GENERAL_RATE_LIMIT, LLM_RATE_LIMIT, limiter
from app.core.security import Principal
from app.db.session import get_session
from app.models.domain import ChallengeTag
from app.schemas.challenge import ChallengeRead, ChallengeRunRequest, ChallengeRunResponse
from app.services import challenges as challenge_service

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
    return challenge_service.list_challenge_reads(session, tag=tag)


@router.get("/{challenge_id}")
@limiter.limit(GENERAL_RATE_LIMIT)
async def get_challenge(
    request: Request,
    response: Response,
    challenge_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ChallengeRead:
    del request, response
    return challenge_service.get_challenge_read(session, challenge_id)


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
    return await challenge_service.run_challenge_prompt(
        session,
        challenge_id=challenge_id,
        run_request=run_request,
        principal=principal,
    )
