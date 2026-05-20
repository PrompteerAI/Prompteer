from starlette.requests import Request

from app.core.ratelimit import limiter, rate_limit_key
from app.core.security import Principal


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
    assert limiter._headers_enabled is True  # noqa: SLF001
    assert limiter._in_memory_fallback_enabled is True  # noqa: SLF001
    assert limiter._key_prefix == "prompteer"  # noqa: SLF001
