"""Persistence helpers for user identity and plan records."""

from sqlmodel import Session, select

from app.models.domain import User, utc_now


def get_user_by_id(session: Session, user_id: str) -> User | None:
    return session.get(User, user_id)


def get_user_by_auth_subject(session: Session, auth_subject: str) -> User | None:
    return session.exec(select(User).where(User.auth_subject == auth_subject)).first()


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def add_user(session: Session, user: User) -> User:
    session.add(user)
    session.flush()
    return user


def mark_user_paid(session: Session, user: User) -> None:
    user.plan = "paid"
    user.updated_at = utc_now()
    session.add(user)
