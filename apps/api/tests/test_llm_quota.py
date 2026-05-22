"""Tests for daily per-user LLM token quota accounting and enforcement."""

from collections.abc import Generator
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

# Import model modules so SQLModel metadata is populated for test databases.
import app.models  # noqa: F401  # Register SQLModel tables before creating test metadata.
from app.api.deps import get_current_principal
from app.core.config import settings
from app.core.errors import ProblemException
from app.core.security import Principal
from app.db.seed import seed
from app.db.session import get_session
from app.main import create_app
from app.models.domain import Challenge, LLMUsageDay, User
from app.services import challenges as challenge_service
from app.services.llm_quota import (
    assert_llm_quota_available,
    current_usage_date,
    record_llm_usage,
    resolve_user_for_principal,
)


@pytest.fixture(autouse=True)
def reset_quota_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_free_daily_token_cap", 50_000)
    monkeypatch.setattr(settings, "llm_paid_daily_token_cap", 500_000)


def test_challenge_run_records_daily_llm_usage() -> None:
    engine = seeded_engine()
    app = create_quota_test_app(engine)
    client = TestClient(app)
    challenge_id = first_challenge_id(engine)

    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={"prompt": "Explain FizzBuzz clearly and write concise Python."},
    )

    assert response.status_code == 200
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "free@prompteer.dev")).one()
        usage = session.get(LLMUsageDay, (user.id, current_usage_date()))
    assert usage is not None
    assert usage.request_count == 1
    assert usage.total_tokens == response.json()["usage"]["total_tokens"]


def test_challenge_run_halts_when_daily_quota_is_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "llm_free_daily_token_cap", 100)
    engine = seeded_engine()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "free@prompteer.dev")).one()
        session.add(
            LLMUsageDay(
                user_id=user.id,
                usage_date=current_usage_date(),
                total_tokens=100,
                prompt_tokens=70,
                completion_tokens=30,
                request_count=2,
            )
        )
        session.commit()

    app = create_quota_test_app(engine)
    client = TestClient(app)
    challenge_id = first_challenge_id(engine)

    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={"prompt": "Explain FizzBuzz clearly and write concise Python."},
    )

    assert response.status_code == 402
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "quota_exceeded"
    assert body["type"] == "https://prompteer.dev/errors/quota-exceeded"


def test_challenge_run_halts_before_provider_when_budget_exceeds_remaining_quota(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "llm_free_daily_token_cap", 1)
    engine = seeded_engine()
    app = create_quota_test_app(engine)
    client = TestClient(app)
    challenge_id = first_challenge_id(engine)
    fake_client = CountingLLMClient()
    monkeypatch.setattr(challenge_service, "get_llm_client", lambda: fake_client)

    response = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={"prompt": "Explain FizzBuzz clearly and write concise Python."},
    )

    assert response.status_code == 402
    assert response.json()["code"] == "quota_exceeded"
    assert fake_client.call_count == 0


def test_quota_preflight_accounts_for_requested_token_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "llm_free_daily_token_cap", 1_000)
    engine = seeded_engine()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "free@prompteer.dev")).one()
        session.add(
            LLMUsageDay(
                user_id=user.id,
                usage_date=current_usage_date(),
                total_tokens=900,
                prompt_tokens=500,
                completion_tokens=400,
                request_count=3,
            )
        )
        session.commit()

        with pytest.raises(ProblemException) as exc_info:
            assert_llm_quota_available(session, user, requested_tokens=200)

    assert exc_info.value.code == "quota_exceeded"


def test_record_llm_usage_does_not_mutate_when_projected_total_exceeds_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "llm_free_daily_token_cap", 100)
    engine = seeded_engine()
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == "free@prompteer.dev")).one()
        session.add(
            LLMUsageDay(
                user_id=user.id,
                usage_date=current_usage_date(),
                total_tokens=90,
                prompt_tokens=60,
                completion_tokens=30,
                request_count=2,
            )
        )
        session.commit()

        with pytest.raises(ProblemException) as exc_info:
            record_llm_usage(
                session,
                user,
                {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            )

    assert exc_info.value.code == "quota_exceeded"
    with Session(engine) as assertion_session:
        user = assertion_session.exec(select(User).where(User.email == "free@prompteer.dev")).one()
        usage = assertion_session.get(LLMUsageDay, (user.id, current_usage_date()))
    assert usage is not None
    assert usage.total_tokens == 90
    assert usage.request_count == 2


def test_resolve_user_for_principal_matches_email_case_insensitively() -> None:
    engine = seeded_engine()

    with Session(engine) as session:
        user = resolve_user_for_principal(
            session,
            Principal(
                subject="mock-google-oauth2|case-variant",
                email=" FREE@PROMPTEER.DEV ",
                is_admin=False,
            ),
        )

    assert user.email == "free@prompteer.dev"
    assert user.id == "00000000-0000-4000-8000-000000000003"


def test_current_usage_date_uses_the_utc_clock() -> None:
    with freeze_time("2026-05-22T23:30:00Z"):
        assert current_usage_date() == date(2026, 5, 22)


def seeded_engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed(session)
    return engine


def create_quota_test_app(engine: Engine) -> FastAPI:
    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_principal] = override_free_principal
    return app


async def override_free_principal() -> Principal:
    return Principal(
        subject="mock-google-oauth2|free",
        email="free@prompteer.dev",
        is_admin=False,
    )


def first_challenge_id(engine: Engine) -> str:
    with Session(engine) as session:
        return session.exec(select(Challenge.id).where(Challenge.challenge_number == 1)).one()


class CountingLLMClient:
    provider = "mock"

    def __init__(self) -> None:
        self.call_count = 0

    async def chat_completion(self, payload: dict[str, object]) -> dict[str, object]:
        self.call_count += 1
        return {
            "choices": [{"message": {"content": "Should not be called."}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    async def anthropic_message(self, payload: dict[str, object]) -> dict[str, object]:
        raise AssertionError(f"Unexpected Anthropic call: {payload}")
