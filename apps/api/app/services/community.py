"""Community board read services that convert repository rows into schemas."""

from datetime import date as LocalDate

from sqlmodel import Session

from app.core.errors import ProblemException
from app.core.time import ensure_utc, local_date_window
from app.models.domain import Challenge, Post, Share, User
from app.repositories import community as community_repository
from app.schemas.community import (
    AuthorRead,
    BoardFeedRead,
    ChallengeSummaryRead,
    DateWindowRead,
    PostRead,
    ShareRead,
)


def read_post(session: Session, post_id: str) -> PostRead:
    return post_to_read(session, load_post(session, post_id))


def read_share(session: Session, share_id: str) -> ShareRead:
    return share_to_read(session, load_public_share(session, share_id))


def read_board_feed(
    session: Session,
    *,
    limit: int,
    date: LocalDate | None,
    timezone: str,
) -> BoardFeedRead:
    date_window = build_date_window(date, timezone)
    posts = community_repository.list_posts(
        session,
        limit=limit,
        start_at=date_window.start_at if date_window is not None else None,
        end_at=date_window.end_at if date_window is not None else None,
    )
    shares = community_repository.list_public_shares(
        session,
        limit=limit,
        start_at=date_window.start_at if date_window is not None else None,
        end_at=date_window.end_at if date_window is not None else None,
    )
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


def load_post(session: Session, post_id: str) -> Post:
    post = community_repository.get_post(session, post_id)
    if post is None:
        raise ProblemException(
            status_code=404,
            title="Post Not Found",
            detail="Community post not found.",
            code="post_not_found",
        )
    return post


def load_public_share(session: Session, share_id: str) -> Share:
    share = community_repository.get_share(session, share_id)
    if share is None or not share.is_public:
        raise ProblemException(
            status_code=404,
            title="Share Not Found",
            detail="Community share not found.",
            code="share_not_found",
        )
    return share


def post_to_read(session: Session, post: Post) -> PostRead:
    author = load_user(session, post.user_id)
    challenge = (
        community_repository.get_challenge(session, post.challenge_id)
        if post.challenge_id
        else None
    )
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
    challenge = community_repository.get_challenge(session, share.challenge_id)
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
    user = community_repository.get_user(session, user_id)
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
