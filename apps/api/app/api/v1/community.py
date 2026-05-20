from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.domain import Challenge, Post, Share, User
from app.schemas.community import (
    AuthorRead,
    BoardFeedRead,
    ChallengeSummaryRead,
    PostRead,
    ShareRead,
)

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/board")
async def read_board_feed(
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> BoardFeedRead:
    posts = session.exec(select(Post).order_by(col(Post.created_at).desc()).limit(limit)).all()
    shares = session.exec(
        select(Share)
        .where(Share.is_public == True)  # noqa: E712
        .order_by(col(Share.created_at).desc())
        .limit(limit)
    ).all()
    return BoardFeedRead(
        posts=[post_to_read(session, post) for post in posts],
        shares=[share_to_read(session, share) for share in shares],
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
        created_at=post.created_at,
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
        created_at=share.created_at,
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
        email=user.email,
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
