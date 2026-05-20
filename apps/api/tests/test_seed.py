from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.db.seed import seed
from app.models.domain import Challenge, Post, Share, User


def test_seed_is_idempotent() -> None:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        seed(session)
        seed(session)

        assert len(session.exec(select(User)).all()) == 3
        assert len(session.exec(select(Challenge)).all()) == 5
        assert len(session.exec(select(Share)).all()) == 3
        assert len(session.exec(select(Post)).all()) == 3
