"""Tests for challenge listing, prompt runs, sharing, quotas, and provider routing."""

import time
from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select
from starlette.requests import Request

# Import model modules so SQLModel metadata is populated for test databases.
import app.models  # noqa: F401  # Register SQLModel tables before creating test metadata.
from app.api.deps import get_current_principal
from app.api.v1 import challenges as challenge_routes
from app.core.config import settings
from app.core.security import Principal
from app.db.seed import seed
from app.db.session import get_session
from app.integrations.llm.base import LLMProviderError
from app.main import create_app
from app.models.domain import Challenge, LLMUsageDay, Share, User
from app.services.llm_quota import current_usage_date
from tests.support import reset_limiter_storage


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    reset_limiter_storage()


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
    assert challenges[0]["references"] == []

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
    assert "raw" not in result
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


def test_list_challenges_includes_media_references_and_empty_ps_references() -> None:
    client, _engine, _challenge_id = create_seeded_challenge_client()

    response = client.get("/api/v1/challenges")

    assert response.status_code == 200
    challenges_by_number = {
        challenge["challenge_number"]: challenge for challenge in response.json()
    }
    assert challenges_by_number[1]["tag"] == "ps"
    assert challenges_by_number[1]["references"] == []
    assert challenges_by_number[2]["tag"] == "img"
    assert challenges_by_number[2]["references"] == [
        {
            "kind": "img",
            "id": challenges_by_number[2]["references"][0]["id"],
            "file_path": "seed/references/product-hero.png",
            "file_type": "image/png",
        }
    ]
    assert challenges_by_number[3]["tag"] == "video"
    assert challenges_by_number[3]["references"] == [
        {
            "kind": "video",
            "id": challenges_by_number[3]["references"][0]["id"],
            "file_path": "seed/references/launch-teaser.mp4",
            "file_type": "video/mp4",
        }
    ]


def test_get_challenge_includes_media_references_and_empty_ps_references() -> None:
    client, _engine, _challenge_id = create_seeded_challenge_client()
    list_response = client.get("/api/v1/challenges")
    assert list_response.status_code == 200
    challenges_by_number = {
        challenge["challenge_number"]: challenge for challenge in list_response.json()
    }

    ps_response = client.get(f"/api/v1/challenges/{challenges_by_number[1]['id']}")
    img_response = client.get(f"/api/v1/challenges/{challenges_by_number[2]['id']}")
    video_response = client.get(f"/api/v1/challenges/{challenges_by_number[3]['id']}")

    assert ps_response.status_code == 200
    assert ps_response.json()["references"] == []
    assert img_response.status_code == 200
    assert img_response.json()["references"] == challenges_by_number[2]["references"]
    assert video_response.status_code == 200
    assert video_response.json()["references"] == challenges_by_number[3]["references"]


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


def test_challenge_run_rolls_back_usage_when_share_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, engine, challenge_id = create_seeded_challenge_client()

    def fail_share_creation(*args: object, **kwargs: object) -> Share:
        raise RuntimeError("share storage unavailable")

    monkeypatch.setattr(challenge_routes, "create_prompt_share", fail_share_creation)

    with pytest.raises(RuntimeError, match="share storage unavailable"):
        client.post(
            f"/api/v1/challenges/{challenge_id}/run",
            json={"prompt": "Explain FizzBuzz clearly and keep the answer compact."},
        )

    with Session(engine) as assertion_session:
        user = assertion_session.exec(select(User).where(User.email == "admin@prompteer.dev")).one()
        usage = assertion_session.get(LLMUsageDay, (user.id, current_usage_date()))

    assert usage is None


def test_challenge_run_updates_existing_public_share_for_user_challenge() -> None:
    client, engine, challenge_id = create_seeded_challenge_client()

    first_response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={"prompt": "Explain FizzBuzz with a compact Python solution."},
    )
    second_response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={"prompt": "Explain FizzBuzz rules before concise Python."},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_share = first_response.json()["share"]
    second_share = second_response.json()["share"]
    assert first_share["id"] == second_share["id"]

    with Session(engine) as assertion_session:
        shares = assertion_session.exec(
            select(Share).where(
                Share.user_id == "00000000-0000-4000-8000-000000000001",
                Share.challenge_id == challenge_id,
            )
        ).all()
        assert len(shares) == 1
        assert shares[0].prompt == "Explain FizzBuzz rules before concise Python."

    board_response = client.get("/api/v1/community/board")

    assert board_response.status_code == 200
    board_shares = board_response.json()["shares"]
    assert board_shares[0]["id"] == second_share["id"]
    assert board_shares[0]["prompt"] == "Explain FizzBuzz rules before concise Python."


def test_mock_challenge_run_returns_within_acceptance_budget() -> None:
    client, _engine, challenge_id = create_seeded_challenge_client()

    started = time.perf_counter()
    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={
            "prompt": "Explain FizzBuzz clearly and keep the answer compact.",
            "publish_to_board": False,
        },
    )
    duration_seconds = time.perf_counter() - started

    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
    assert duration_seconds < 2.0


def test_challenge_run_uses_configured_openai_model(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _engine, challenge_id = create_seeded_challenge_client()
    fake_client = CapturingOpenAIClient()
    monkeypatch.setattr(challenge_routes, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(settings, "openai_chat_model", "gpt-4.1-mini")

    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={
            "prompt": "Explain FizzBuzz clearly and write compact Python.",
            "publish_to_board": False,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["provider"] == "openai"
    assert result["output"] == "OpenAI feedback"
    assert result["usage"] == {
        "prompt_tokens": 11,
        "completion_tokens": 7,
        "total_tokens": 18,
    }
    assert fake_client.payload is not None
    assert fake_client.payload["model"] == "gpt-4.1-mini"
    assert fake_client.payload["max_completion_tokens"] == 512


def test_challenge_run_supports_real_anthropic_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _engine, challenge_id = create_seeded_challenge_client()
    fake_client = CapturingAnthropicClient()
    monkeypatch.setattr(challenge_routes, "get_llm_client", lambda: fake_client)
    monkeypatch.setattr(settings, "anthropic_model", "claude-sonnet-4-20250514")

    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={
            "prompt": "Explain FizzBuzz clearly and write compact Python.",
            "publish_to_board": False,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["provider"] == "anthropic"
    assert result["output"] == "Anthropic feedback"
    assert result["usage"] == {
        "prompt_tokens": 13,
        "completion_tokens": 5,
        "total_tokens": 18,
        "input_tokens": 13,
        "output_tokens": 5,
    }
    assert fake_client.payload is not None
    assert fake_client.payload["model"] == "claude-sonnet-4-20250514"
    assert fake_client.payload["max_tokens"] == 512
    assert fake_client.payload["messages"][0]["role"] == "user"


def test_challenge_run_returns_problem_details_for_provider_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _engine, challenge_id = create_seeded_challenge_client()
    monkeypatch.setattr(challenge_routes, "get_llm_client", lambda: FailingOpenAIClient())

    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={
            "prompt": "Explain FizzBuzz clearly and write compact Python.",
            "publish_to_board": False,
        },
    )

    assert response.status_code == 502
    assert response.headers["content-type"].startswith("application/problem+json")
    problem = response.json()
    assert problem["code"] == "llm_provider_error"
    assert problem["title"] == "LLM Provider Error"
    assert "provider unavailable" in problem["detail"]


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
    assert response.json()["code"] == "unauthorized"


def test_challenge_run_rate_limit_is_scoped_to_authenticated_user() -> None:
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

    current_principal = Principal(
        subject="mock-google-oauth2|free",
        email="free@prompteer.dev",
        is_admin=False,
    )

    async def override_rate_principal(request: Request) -> Principal:
        request.state.principal = current_principal
        return current_principal

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_principal] = override_rate_principal
    client = TestClient(app)

    for run_index in range(10):
        response = client.post(
            f"/api/v1/challenges/{challenge_id}/run",
            json={
                "prompt": f"Explain FizzBuzz clearly and write Python attempt {run_index}.",
                "publish_to_board": False,
            },
        )
        assert response.status_code == 200

    limited = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={
            "prompt": "Explain FizzBuzz clearly and write Python after the limit.",
            "publish_to_board": False,
        },
    )

    assert limited.status_code == 429
    assert limited.headers["content-type"].startswith("application/problem+json")
    assert "retry-after" in limited.headers
    assert limited.json()["code"] == "rate_limited"

    current_principal = Principal(
        subject="mock-google-oauth2|paid",
        email="paid@prompteer.dev",
        is_admin=False,
    )
    paid_user_response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={
            "prompt": "Explain FizzBuzz clearly and write Python as a paid user.",
            "publish_to_board": False,
        },
    )

    assert paid_user_response.status_code == 200


async def override_principal() -> Principal:
    return Principal(
        subject="mock-google-oauth2|admin",
        email="admin@prompteer.dev",
        is_admin=True,
    )


def create_seeded_challenge_client() -> tuple[TestClient, Engine, str]:
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
    app.dependency_overrides[get_current_principal] = override_principal
    return TestClient(app), engine, challenge_id


class CapturingOpenAIClient:
    provider = "openai"

    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payload = payload
        return {
            "id": "chatcmpl_real_test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "OpenAI feedback"},
                    "finish_reason": "stop",
                    "logprobs": None,
                }
            ],
            "usage": {
                "prompt_tokens": 11,
                "completion_tokens": 7,
                "total_tokens": 18,
            },
        }

    async def anthropic_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError(f"Unexpected Anthropic call: {payload}")


class CapturingAnthropicClient:
    provider = "anthropic"

    def __init__(self) -> None:
        self.payload: dict[str, Any] | None = None

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError(f"Unexpected OpenAI call: {payload}")

    async def anthropic_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payload = payload
        return {
            "id": "msg_real_test",
            "type": "message",
            "role": "assistant",
            "model": payload["model"],
            "content": [{"type": "text", "text": "Anthropic feedback"}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 13, "output_tokens": 5},
        }


class FailingOpenAIClient:
    provider = "openai"

    async def chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise LLMProviderError(provider=self.provider, detail="provider unavailable")

    async def anthropic_message(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise AssertionError(f"Unexpected Anthropic call: {payload}")
