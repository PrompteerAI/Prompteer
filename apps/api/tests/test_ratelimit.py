"""Tests for rate-limit keying, headers, fallback behavior, and 429 responses."""

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.ratelimit import limiter, rate_limit_key
from app.core.security import Principal
from app.main import create_app
from tests.support import reset_limiter_storage


@pytest.fixture(autouse=True)
def reset_limiter() -> None:
    reset_limiter_storage()


def request_for_ip(address: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
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


def test_limiter_is_configured_for_headers_and_fallback() -> None:
    assert limiter._headers_enabled is True
    assert limiter._in_memory_fallback_enabled is True
    assert limiter._key_prefix == "prompteer"
    assert limiter._storage_uri is not None
    assert limiter._storage_uri.startswith("redis://")


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
