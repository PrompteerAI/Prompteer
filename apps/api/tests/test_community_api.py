"""Tests for community board feed and detail behavior."""

from collections.abc import Generator
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

# Import model modules so SQLModel metadata is populated for test databases.
import app.models  # noqa: F401
from app.db.seed import seed
from app.db.session import get_session
from app.main import create_app
from app.models.domain import Post, Share


def test_get_seeded_post_returns_post_read() -> None:
    client, engine = seeded_client()
    with Session(engine) as session:
        post = session.exec(select(Post).order_by(Post.title)).first()
        assert post is not None

    response = client.get(f"/api/v1/community/posts/{post.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == post.id
    assert payload["title"] == post.title
    assert "email" not in payload["author"]
    assert payload["challenge"]["title"]


def test_get_seeded_public_share_returns_share_read() -> None:
    client, engine = seeded_client()
    with Session(engine) as session:
        share = session.exec(select(Share).where(Share.is_public).order_by(Share.id)).first()
        assert share is not None

    response = client.get(f"/api/v1/community/shares/{share.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == share.id
    assert payload["is_public"] is True
    assert "email" not in payload["author"]
    assert payload["challenge"]["title"]


def test_get_missing_post_returns_problem_details() -> None:
    client, _engine = seeded_client()

    response = client.get("/api/v1/community/posts/00000000-0000-4000-8000-999999999999")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "post_not_found"


def test_get_missing_share_returns_problem_details() -> None:
    client, _engine = seeded_client()

    response = client.get("/api/v1/community/shares/00000000-0000-4000-8000-999999999999")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "share_not_found"


def test_get_private_share_returns_not_found_problem_details() -> None:
    client, engine = seeded_client()
    with Session(engine) as session:
        share = session.exec(select(Share).where(Share.is_public).order_by(Share.id)).first()
        assert share is not None
        share.is_public = False
        session.add(share)
        session.commit()
        share_id = share.id

    response = client.get(f"/api/v1/community/shares/{share_id}")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "share_not_found"


def test_board_feed_returns_seed_posts_and_shares() -> None:
    client, _engine = seeded_client()

    response = client.get("/api/v1/community/board")

    assert response.status_code == 200
    feed = response.json()
    assert len(feed["posts"]) == 3
    assert len(feed["shares"]) == 3
    assert all("email" not in post["author"] for post in feed["posts"])
    assert all("email" not in share["author"] for share in feed["shares"])
    assert feed["shares"][0]["challenge"]["title"]


def seeded_client() -> tuple[TestClient, Engine]:
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
    return TestClient(app), engine


def test_board_feed_filters_by_user_local_date_and_returns_utc_window() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as seed_session:
        seed(seed_session)
        posts = seed_session.exec(select(Post).order_by(Post.title)).all()
        shares = seed_session.exec(select(Share).order_by(Share.id)).all()
        for post in posts:
            post.created_at = datetime(2026, 5, 19, 12, tzinfo=UTC)
        for share in shares:
            share.created_at = datetime(2026, 5, 19, 12, tzinfo=UTC)
        posts[0].created_at = datetime(2026, 5, 20, 8, 30, tzinfo=UTC)
        shares[0].created_at = datetime(2026, 5, 21, 6, 30, tzinfo=UTC)
        seed_session.commit()

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    response = client.get(
        "/api/v1/community/board",
        params={"date": "2026-05-20", "timezone": "America/Los_Angeles"},
    )

    assert response.status_code == 200
    feed = response.json()
    assert feed["date_window"]["date"] == "2026-05-20"
    assert feed["date_window"]["timezone"] == "America/Los_Angeles"
    assert parse_iso_datetime(feed["date_window"]["start_at"]) == datetime(
        2026, 5, 20, 7, tzinfo=UTC
    )
    assert parse_iso_datetime(feed["date_window"]["end_at"]) == datetime(2026, 5, 21, 7, tzinfo=UTC)
    assert len(feed["posts"]) == 1
    assert len(feed["shares"]) == 1
    assert parse_iso_datetime(feed["posts"][0]["created_at"]).tzinfo is not None
    assert parse_iso_datetime(feed["shares"][0]["created_at"]).tzinfo is not None


def test_board_feed_rejects_unknown_timezone() -> None:
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/community/board",
        params={"date": "2026-05-20", "timezone": "Mars/Olympus"},
    )

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "invalid_timezone"


def parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
