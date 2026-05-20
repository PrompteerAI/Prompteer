from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.db.seed import seed
from app.db.session import get_session
from app.main import create_app


def test_board_feed_returns_seed_posts_and_shares() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as seed_session:
        seed(seed_session)

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    response = client.get("/api/v1/community/board")

    assert response.status_code == 200
    feed = response.json()
    assert len(feed["posts"]) == 3
    assert len(feed["shares"]) == 3
    assert {post["author"]["email"] for post in feed["posts"]} == {
        "admin@prompteer.dev",
        "paid@prompteer.dev",
        "free@prompteer.dev",
    }
    assert feed["shares"][0]["challenge"]["title"]
