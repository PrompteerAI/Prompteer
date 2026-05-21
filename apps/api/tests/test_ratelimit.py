"""Tests for rate-limit keying, headers, storage, and 429 responses."""

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core.config import settings
from app.core.ratelimit import limiter, rate_limit_key, trusted_proxy_networks
from app.core.security import Principal
from app.main import create_app
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
