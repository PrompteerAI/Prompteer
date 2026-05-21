"""API v1 community routes; no sibling community API version exists yet."""

from datetime import date as LocalDate
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlmodel import Session, col, select

from app.core.errors import ProblemException
from app.core.ratelimit import GENERAL_RATE_LIMIT, limiter
from app.core.time import ensure_utc, local_date_window
from app.db.session import get_session
from app.models.domain import Challenge, Post, Share, User
from app.schemas.community import (
    AuthorRead,
    BoardFeedRead,
    ChallengeSummaryRead,
    DateWindowRead,
    PostRead,
    ShareRead,
)

router = APIRouter(prefix="/community", tags=["community"])


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
    date_window = build_date_window(date, timezone)
    posts_statement = select(Post)
    shares_statement = select(Share).where(col(Share.is_public).is_(True))
    if date_window is not None:
        posts_statement = posts_statement.where(
            col(Post.created_at) >= date_window.start_at,
            col(Post.created_at) < date_window.end_at,
        )
        shares_statement = shares_statement.where(
            col(Share.created_at) >= date_window.start_at,
            col(Share.created_at) < date_window.end_at,
        )
    posts = session.exec(posts_statement.order_by(col(Post.created_at).desc()).limit(limit)).all()
    shares = session.exec(
        shares_statement.order_by(col(Share.updated_at).desc(), col(Share.created_at).desc()).limit(
            limit
        )
    ).all()
    return BoardFeedRead(
        posts=[post_to_read(session, post) for post in posts],
        shares=[share_to_read(session, share) for share in shares],
        date_window=date_window,
    )


def build_date_window(local_date: LocalDate | None, timezone_name: str) -> DateWindowRead | None:
    if local_date is None:
        return None
    try:
        start_at, end_at = local_date_window(local_date, timezone_name)
    except ValueError as exc:
        raise ProblemException(
            status_code=400,
            title="Invalid timezone",
            detail=str(exc),
            code="invalid_timezone",
        ) from exc
    return DateWindowRead(
        date=local_date,
        timezone=timezone_name,
        start_at=start_at,
        end_at=end_at,
    )


def post_to_read(session: Session, post: Post) -> PostRead:
    author = load_user(session, post.user_id)
    challenge = session.get(Challenge, post.challenge_id) if post.challenge_id else None
    return PostRead(
        id=post.id,
        type=post.type,
        tag=post.tag,
        title=post.title,
        content=post.content,
        author=author_to_read(author),
        challenge=challenge_to_read(challenge) if challenge else None,
        created_at=ensure_utc(post.created_at),
    )


def share_to_read(session: Session, share: Share) -> ShareRead:
    author = load_user(session, share.user_id)
    challenge = session.get(Challenge, share.challenge_id)
    if challenge is None:
        raise RuntimeError(f"Share {share.id} references a missing challenge.")
    return ShareRead(
        id=share.id,
        prompt=share.prompt,
        is_public=share.is_public,
        author=author_to_read(author),
        challenge=challenge_to_read(challenge),
        created_at=ensure_utc(share.created_at),
    )


def load_user(session: Session, user_id: str) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise RuntimeError(f"Missing user {user_id}.")
    return user


def author_to_read(user: User) -> AuthorRead:
    return AuthorRead(
        id=user.id,
        display_name=user.display_name,
        plan=user.plan,
    )


def challenge_to_read(challenge: Challenge) -> ChallengeSummaryRead:
    return ChallengeSummaryRead(
        id=challenge.id,
        challenge_number=challenge.challenge_number,
        tag=challenge.tag,
        level=challenge.level,
        title=challenge.title,
    )
