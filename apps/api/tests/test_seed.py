"""Tests for idempotent local demo seed data."""

from sqlmodel import Session, SQLModel, create_engine, select

# Import model modules so SQLModel metadata is populated for test databases.
import app.models  # noqa: F401  # Register SQLModel tables before creating test metadata.
from app.db.seed import seed
from app.integrations.payments.mock import STORE
from app.models.domain import Challenge, Post, Profile, Share, StripeCheckoutSession, User


def test_seed_is_idempotent() -> None:
    STORE.reset()
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        seed(session)
        seed(session)

        assert len(session.exec(select(User)).all()) == 3
        assert len(session.exec(select(Profile)).all()) == 3
        assert len(session.exec(select(Challenge)).all()) == 5
        assert len(session.exec(select(Share)).all()) == 3
        assert len(session.exec(select(Post)).all()) == 3
        assert len(session.exec(select(StripeCheckoutSession)).all()) == 2
        assert len(STORE.sessions) == 2
        assert len(STORE.events) == 2
        assert {
            checkout_session.customer_email
            for checkout_session in session.exec(select(StripeCheckoutSession)).all()
            if checkout_session.status == "complete"
            and checkout_session.payment_status == "paid"
            and checkout_session.mode == "subscription"
        } == {"admin@prompteer.dev", "paid@prompteer.dev"}
        assert {
            checkout_session["customer_email"]
            for checkout_session in STORE.sessions.values()
            if checkout_session["status"] == "complete"
            and checkout_session["payment_status"] == "paid"
            and checkout_session["mode"] == "subscription"
        } == {"admin@prompteer.dev", "paid@prompteer.dev"}
