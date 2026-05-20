from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.api.deps import get_current_principal
from app.core.security import Principal
from app.db.seed import seed
from app.db.session import get_session
from app.main import create_app
from app.models.domain import Challenge, Share


def test_list_and_run_seeded_coding_challenge() -> None:
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
    app.dependency_overrides[get_current_principal] = override_principal
    client = TestClient(app)

    list_response = client.get("/api/v1/challenges", params={"tag": "ps"})
    assert list_response.status_code == 200
    challenges = list_response.json()
    assert len(challenges) == 3
    assert challenges[0]["title"] == "FizzBuzz prompt repair"

    run_response = client.post(
        f"/api/v1/challenges/{challenges[0]['id']}/run",
        json={
            "prompt": "Explain the FizzBuzz rules, then produce a concise Python solution.",
        },
    )

    assert run_response.status_code == 200
    result = run_response.json()
    assert result["challenge"]["id"] == challenges[0]["id"]
    assert result["provider"] == "mock"
    assert "Mock Prompteer response" in result["output"]
    assert result["usage"]["total_tokens"] >= result["usage"]["completion_tokens"]
    assert result["share"]["is_public"] is True

    with Session(engine) as assertion_session:
        created_share = assertion_session.get(Share, result["share"]["id"])
        assert created_share is not None
        assert created_share.user_id == "00000000-0000-4000-8000-000000000001"
        assert created_share.prompt == (
            "Explain the FizzBuzz rules, then produce a concise Python solution."
        )

    board_response = client.get("/api/v1/community/board")
    assert board_response.status_code == 200
    assert any(share["id"] == result["share"]["id"] for share in board_response.json()["shares"])


def test_challenge_run_can_skip_public_share_creation() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as seed_session:
        seed(seed_session)
        challenge_id = seed_session.exec(
            select(Challenge.id).where(Challenge.challenge_number == 1)
        ).one()
        before_count = len(seed_session.exec(select(Share)).all())

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_principal] = override_principal
    client = TestClient(app)

    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={
            "prompt": "Explain FizzBuzz clearly and keep the answer compact.",
            "publish_to_board": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["share"] is None
    with Session(engine) as assertion_session:
        after_count = len(assertion_session.exec(select(Share)).all())
    assert after_count == before_count


def test_challenge_run_requires_authentication() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as seed_session:
        seed(seed_session)
        challenge_id = seed_session.exec(
            select(Challenge.id).where(Challenge.challenge_number == 1)
        ).one()

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={"prompt": "Explain FizzBuzz clearly and write Python."},
    )

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "http_error"


async def override_principal() -> Principal:
    return Principal(
        subject="mock-google-oauth2|admin",
        email="admin@prompteer.dev",
        is_admin=True,
    )
