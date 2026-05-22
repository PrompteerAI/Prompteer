"""API v1 community routes; no sibling community API version exists yet."""

from datetime import date as LocalDate
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlmodel import Session

from app.core.ratelimit import GENERAL_RATE_LIMIT, limiter
from app.db.session import get_session
from app.schemas.community import BoardFeedRead, PostRead, ShareRead
from app.services import community as community_service

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/posts/{post_id}")
@limiter.limit(GENERAL_RATE_LIMIT)
async def read_post(
    request: Request,
    response: Response,
    post_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> PostRead:
    del request, response
    return community_service.read_post(session, post_id)


@router.get("/shares/{share_id}")
@limiter.limit(GENERAL_RATE_LIMIT)
async def read_share(
    request: Request,
    response: Response,
    share_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> ShareRead:
    del request, response
    return community_service.read_share(session, share_id)


@router.get("/board")
@limiter.limit(GENERAL_RATE_LIMIT)
async def read_board_feed(
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    date: Annotated[
        LocalDate | None,
        Query(description="Optional user-local board date to filter."),
    ] = None,
    timezone: Annotated[
        str,
        Query(min_length=1, max_length=64, description="IANA timezone for the date filter."),
    ] = "UTC",
) -> BoardFeedRead:
    del request, response
    return community_service.read_board_feed(
        session,
        limit=limit,
        date=date,
        timezone=timezone,
    )
