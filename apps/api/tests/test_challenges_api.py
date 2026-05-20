from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.db.seed import seed
from app.db.session import get_session
from app.main import create_app


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
