"""Tests for rate-limit keying, headers, storage, and 429 responses."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select
from starlette.requests import Request

import app.models  # noqa: F401  # Register SQLModel tables before creating test metadata.
from app.api.deps import get_current_principal
from app.core.config import settings
from app.core.ratelimit import limiter, rate_limit_key, trusted_proxy_networks
from app.core.security import Principal
from app.db.seed import seed
from app.db.session import get_session
from app.main import create_app
from app.models.domain import Challenge
from tests.support import reset_limiter_storage


@pytest.fixture(autouse=True)
def reset_limiter() -> None:
    reset_limiter_storage()


def request_for_ip(address: str, *, headers: dict[str, str] | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [
                (name.lower().encode("latin-1"), value.encode("latin-1"))
                for name, value in (headers or {}).items()
            ],
            "client": (address, 12345),
        }
    )


def test_rate_limit_key_prefers_authenticated_principal() -> None:
    request = request_for_ip("203.0.113.10")
    request.state.principal = Principal(
        subject="mock-google-oauth2|admin",
        email="admin@prompteer.dev",
        is_admin=True,
    )

    assert rate_limit_key(request) == "user:mock-google-oauth2|admin"


def test_rate_limit_key_falls_back_to_remote_ip() -> None:
    request = request_for_ip("203.0.113.11")

    assert rate_limit_key(request) == "ip:203.0.113.11"


def test_rate_limit_key_uses_forwarded_for_from_trusted_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "rate_limit_trusted_proxy_cidrs", "172.16.0.0/12")
    trusted_proxy_networks.cache_clear()
    request = request_for_ip(
        "172.18.0.12",
        headers={"x-forwarded-for": "198.51.100.8, 172.18.0.12"},
    )

    assert rate_limit_key(request) == "ip:198.51.100.8"


def test_rate_limit_key_ignores_spoofed_forwarded_for_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "rate_limit_trusted_proxy_cidrs", "172.16.0.0/12")
    trusted_proxy_networks.cache_clear()
    request = request_for_ip(
        "172.18.0.12",
        headers={"x-forwarded-for": "198.51.100.250, 203.0.113.42"},
    )

    assert rate_limit_key(request) == "ip:203.0.113.42"


def test_rate_limit_key_ignores_forwarded_for_from_untrusted_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "rate_limit_trusted_proxy_cidrs", "172.16.0.0/12")
    trusted_proxy_networks.cache_clear()
    request = request_for_ip(
        "203.0.113.12",
        headers={"x-forwarded-for": "198.51.100.8"},
    )

    assert rate_limit_key(request) == "ip:203.0.113.12"


def test_limiter_is_configured_for_headers_and_external_storage() -> None:
    assert limiter._headers_enabled is True
    assert limiter._in_memory_fallback_enabled is False
    assert limiter._key_prefix == "prompteer"
    assert limiter._storage_uri == settings.rate_limit_storage_url


def test_auth_dependency_attempts_are_rate_limited_before_jwt_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "auth_attempt_rate_limit", "2/minute")
    client = TestClient(create_app())

    assert client.get("/api/v1/billing/subscription").status_code == 401
    assert client.get("/api/v1/billing/subscription").status_code == 401
    limited = client.get("/api/v1/billing/subscription")

    assert limited.status_code == 429
    assert limited.headers["content-type"].startswith("application/problem+json")
    assert "retry-after" in limited.headers
    assert limited.json()["code"] == "rate_limited"


def test_llm_rate_limit_returns_problem_details_with_retry_after() -> None:
    client = TestClient(create_app())
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": "Improve this prompt."}],
    }

    for _ in range(10):
        response = client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200

    limited = client.post("/v1/chat/completions", json=payload)

    assert limited.status_code == 429
    assert limited.headers["content-type"].startswith("application/problem+json")
    assert "retry-after" in limited.headers
    assert limited.json()["code"] == "rate_limited"


def test_free_user_challenge_run_llm_rate_limit_returns_problem_details() -> None:
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

    async def override_free_principal(request: Request) -> Principal:
        principal = Principal(
            subject="mock-google-oauth2|free",
            email="free@prompteer.dev",
            is_admin=False,
        )
        request.state.principal = principal
        return principal

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_principal] = override_free_principal
    client = TestClient(app)

    for run_index in range(10):
        response = client.post(
            f"/api/v1/challenges/{challenge_id}/run",
            json={
                "prompt": (
                    "Explain FizzBuzz clearly and write a compact Python solution "
                    f"for free user attempt {run_index}."
                ),
                "publish_to_board": False,
            },
        )
        assert response.status_code == 200

    limited = client.post(
        f"/api/v1/challenges/{challenge_id}/run",
        json={
            "prompt": (
                "Explain FizzBuzz clearly and write a compact Python solution "
                "after the free user limit."
            ),
            "publish_to_board": False,
        },
    )

    assert limited.status_code == 429
    assert limited.headers["content-type"].startswith("application/problem+json")
    retry_after = limited.headers.get("retry-after")
    assert retry_after is not None
    assert retry_after.isdecimal()
    assert int(retry_after) > 0
    problem = limited.json()
    assert problem["type"] == "https://prompteer.dev/errors/rate-limited"
    assert problem["title"] == "Too Many Requests"
    assert problem["status"] == 429
    assert problem["instance"] == f"/api/v1/challenges/{challenge_id}/run"
    assert problem["code"] == "rate_limited"
    assert problem["request_id"] is not None
