"""Persistence helpers for community board posts and shared prompt runs."""

from datetime import datetime

from sqlmodel import Session, col, select

from app.models.domain import Challenge, Post, Share, User


def get_post(session: Session, post_id: str) -> Post | None:
    return session.get(Post, post_id)


def get_share(session: Session, share_id: str) -> Share | None:
    return session.get(Share, share_id)


def get_user(session: Session, user_id: str) -> User | None:
    return session.get(User, user_id)


def get_challenge(session: Session, challenge_id: str) -> Challenge | None:
    return session.get(Challenge, challenge_id)


def list_posts(
    session: Session,
    *,
    limit: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[Post]:
    statement = select(Post)
    if start_at is not None and end_at is not None:
        statement = statement.where(col(Post.created_at) >= start_at, col(Post.created_at) < end_at)
    return list(session.exec(statement.order_by(col(Post.created_at).desc()).limit(limit)).all())


def list_public_shares(
    session: Session,
    *,
    limit: int,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[Share]:
    statement = select(Share).where(col(Share.is_public).is_(True))
    if start_at is not None and end_at is not None:
        statement = statement.where(
            col(Share.created_at) >= start_at,
            col(Share.created_at) < end_at,
        )
    return list(
        session.exec(
            statement.order_by(col(Share.updated_at).desc(), col(Share.created_at).desc()).limit(
                limit
            )
        ).all()
    )
