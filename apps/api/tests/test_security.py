"""Tests for Auth.js-issued API bearer token verification."""

import base64
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from fastapi import HTTPException
from starlette.requests import Request

from app.api.deps import get_current_principal
from app.core import security
from app.core.config import settings
from app.core.security import (
    AuthTokenError,
    clear_jwks_cache,
    verify_bearer_token,
    verify_jwt_with_jwks,
)


@pytest.fixture(autouse=True)
def reset_jwks_cache() -> None:
    clear_jwks_cache()


def test_verify_jwt_with_jwks_returns_principal() -> None:
    private_key: RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    token = sign_test_token(private_key)

    principal = verify_jwt_with_jwks(
        token,
        {"keys": [public_jwk(public_key)]},
        issuer="http://localhost:3000",
        audience="prompteer-api",
    )

    assert principal.subject == "mock-google-oauth2|admin"
    assert principal.email == "admin@prompteer.dev"
    assert principal.is_admin is True


def test_verify_jwt_with_jwks_rejects_wrong_audience() -> None:
    private_key: RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = sign_test_token(private_key)

    with pytest.raises(AuthTokenError):
        verify_jwt_with_jwks(
            token,
            {"keys": [public_jwk(private_key.public_key())]},
            issuer="http://localhost:3000",
            audience="wrong-audience",
        )


def test_verify_jwt_with_jwks_rejects_missing_expiration() -> None:
    private_key: RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    now = datetime.now(tz=UTC)
    token = jwt.encode(
        {
            "iss": "http://localhost:3000",
            "aud": "prompteer-api",
            "sub": "mock-google-oauth2|admin",
            "email": "admin@prompteer.dev",
            "iat": int(now.timestamp()),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )

    with pytest.raises(AuthTokenError):
        verify_jwt_with_jwks(
            token,
            {"keys": [public_jwk(public_key)]},
            issuer="http://localhost:3000",
            audience="prompteer-api",
        )


@pytest.mark.asyncio
async def test_get_current_principal_requires_bearer_token() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_principal(request_for_auth())

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
async def test_verify_bearer_token_caches_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key: RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    calls: list[str] = []

    async def fake_fetch_jwks(jwks_url: str) -> dict[str, Any]:
        calls.append(jwks_url)
        return {"keys": [public_jwk(private_key.public_key())]}

    monkeypatch.setattr(security, "fetch_jwks", fake_fetch_jwks)
    token = sign_test_token(private_key)

    first = await verify_bearer_token(token)
    second = await verify_bearer_token(token)

    assert first.subject == "mock-google-oauth2|admin"
    assert second.subject == "mock-google-oauth2|admin"
    assert calls == ["http://localhost:3000/api/auth/jwks"]


@pytest.mark.asyncio
async def test_verify_bearer_token_refetches_jwks_on_unknown_kid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    second_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    keysets = [
        {"keys": [public_jwk(first_private_key.public_key(), kid="old-key")]},
        {"keys": [public_jwk(second_private_key.public_key(), kid="new-key")]},
    ]
    calls: list[str] = []

    async def fake_fetch_jwks(jwks_url: str) -> dict[str, Any]:
        calls.append(jwks_url)
        return keysets.pop(0)

    monkeypatch.setattr(security, "fetch_jwks", fake_fetch_jwks)
    await verify_bearer_token(sign_test_token(first_private_key, kid="old-key"))

    principal = await verify_bearer_token(sign_test_token(second_private_key, kid="new-key"))

    assert principal.subject == "mock-google-oauth2|admin"
    assert calls == [
        "http://localhost:3000/api/auth/jwks",
        "http://localhost:3000/api/auth/jwks",
    ]


@pytest.mark.asyncio
async def test_verify_bearer_token_refetches_jwks_on_same_kid_signature_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    second_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    keysets = [
        {"keys": [public_jwk(first_private_key.public_key(), kid="rotated-key")]},
        {"keys": [public_jwk(second_private_key.public_key(), kid="rotated-key")]},
    ]
    calls: list[str] = []

    async def fake_fetch_jwks(jwks_url: str) -> dict[str, Any]:
        calls.append(jwks_url)
        return keysets.pop(0)

    monkeypatch.setattr(security, "fetch_jwks", fake_fetch_jwks)
    await verify_bearer_token(sign_test_token(first_private_key, kid="rotated-key"))

    principal = await verify_bearer_token(sign_test_token(second_private_key, kid="rotated-key"))

    assert principal.subject == "mock-google-oauth2|admin"
    assert calls == [
        "http://localhost:3000/api/auth/jwks",
        "http://localhost:3000/api/auth/jwks",
    ]


@pytest.mark.asyncio
async def test_verify_bearer_token_rejects_invalid_same_kid_token_after_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trusted_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    untrusted_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    calls: list[str] = []

    async def fake_fetch_jwks(jwks_url: str) -> dict[str, Any]:
        calls.append(jwks_url)
        return {"keys": [public_jwk(trusted_private_key.public_key(), kid="stable-key")]}

    monkeypatch.setattr(security, "fetch_jwks", fake_fetch_jwks)
    await verify_bearer_token(sign_test_token(trusted_private_key, kid="stable-key"))

    with pytest.raises(AuthTokenError, match=security.SIGNATURE_MISMATCH_ERROR):
        await verify_bearer_token(sign_test_token(untrusted_private_key, kid="stable-key"))

    assert calls == [
        "http://localhost:3000/api/auth/jwks",
        "http://localhost:3000/api/auth/jwks",
    ]


@pytest.mark.asyncio
async def test_verify_bearer_token_does_not_refetch_same_kid_mismatch_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "env", "production")
    first_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    second_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    calls: list[str] = []

    async def fake_fetch_jwks(jwks_url: str) -> dict[str, Any]:
        calls.append(jwks_url)
        return {"keys": [public_jwk(first_private_key.public_key(), kid="rotated-key")]}

    monkeypatch.setattr(security, "fetch_jwks", fake_fetch_jwks)
    await verify_bearer_token(sign_test_token(first_private_key, kid="rotated-key"))

    with pytest.raises(AuthTokenError, match=security.SIGNATURE_MISMATCH_ERROR):
        await verify_bearer_token(sign_test_token(second_private_key, kid="rotated-key"))

    assert calls == ["http://localhost:3000/api/auth/jwks"]


@pytest.mark.asyncio
async def test_verify_bearer_token_does_not_refetch_same_kid_mismatch_in_staging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "env", "staging")
    first_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    second_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    calls: list[str] = []

    async def fake_fetch_jwks(jwks_url: str) -> dict[str, Any]:
        calls.append(jwks_url)
        return {"keys": [public_jwk(first_private_key.public_key(), kid="rotated-key")]}

    monkeypatch.setattr(security, "fetch_jwks", fake_fetch_jwks)
    await verify_bearer_token(sign_test_token(first_private_key, kid="rotated-key"))

    with pytest.raises(AuthTokenError, match=security.SIGNATURE_MISMATCH_ERROR):
        await verify_bearer_token(sign_test_token(second_private_key, kid="rotated-key"))

    assert calls == ["http://localhost:3000/api/auth/jwks"]


@pytest.mark.asyncio
async def test_verify_bearer_token_backs_off_repeated_unknown_kid_refreshes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key: RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    unknown_private_key: RSAPrivateKey = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    calls: list[str] = []

    async def fake_fetch_jwks(jwks_url: str) -> dict[str, Any]:
        calls.append(jwks_url)
        return {"keys": [public_jwk(private_key.public_key(), kid="stable-key")]}

    monkeypatch.setattr(security, "fetch_jwks", fake_fetch_jwks)
    await verify_bearer_token(sign_test_token(private_key, kid="stable-key"))

    with pytest.raises(AuthTokenError, match=security.NO_MATCHING_KID_ERROR):
        await verify_bearer_token(sign_test_token(unknown_private_key, kid="random-key-1"))
    with pytest.raises(AuthTokenError, match=security.NO_MATCHING_KID_ERROR):
        await verify_bearer_token(sign_test_token(unknown_private_key, kid="random-key-2"))

    assert calls == [
        "http://localhost:3000/api/auth/jwks",
        "http://localhost:3000/api/auth/jwks",
    ]


@pytest.mark.asyncio
async def test_fetch_jwks_retries_transient_transport_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FlakyAsyncClient:
        calls = 0

        def __init__(self, *, timeout: float) -> None:
            assert timeout == security.JWKS_FETCH_TIMEOUT_SECONDS

        async def __aenter__(self) -> "FlakyAsyncClient":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def get(self, _url: str) -> httpx.Response:
            type(self).calls += 1
            if type(self).calls == 1:
                raise httpx.ReadTimeout("cold JWKS route")
            return httpx.Response(
                200,
                json={"keys": []},
                request=httpx.Request("GET", _url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", FlakyAsyncClient)

    assert await security.fetch_jwks("http://localhost:3000/api/auth/jwks") == {"keys": []}
    assert FlakyAsyncClient.calls == 2


@pytest.mark.asyncio
async def test_fetch_jwks_wraps_transport_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            assert timeout == security.JWKS_FETCH_TIMEOUT_SECONDS

        async def __aenter__(self) -> "FailingAsyncClient":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def get(self, _url: str) -> httpx.Response:
            raise httpx.ReadTimeout("unreachable JWKS route")

    monkeypatch.setattr(httpx, "AsyncClient", FailingAsyncClient)

    with pytest.raises(AuthTokenError, match="JWKS endpoint was unreachable"):
        await security.fetch_jwks("http://localhost:3000/api/auth/jwks")


@pytest.mark.asyncio
async def test_fetch_jwks_wraps_malformed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InvalidJsonAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            assert timeout == security.JWKS_FETCH_TIMEOUT_SECONDS

        async def __aenter__(self) -> "InvalidJsonAsyncClient":
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"not-json",
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", InvalidJsonAsyncClient)

    with pytest.raises(AuthTokenError, match="JWKS endpoint returned invalid JSON"):
        await security.fetch_jwks("http://localhost:3000/api/auth/jwks")


def request_for_auth() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": []})


def sign_test_token(private_key: RSAPrivateKey, *, kid: str = "test-key") -> str:
    now = datetime.now(tz=UTC)
    return jwt.encode(
        {
            "iss": "http://localhost:3000",
            "aud": "prompteer-api",
            "sub": "mock-google-oauth2|admin",
            "email": "admin@prompteer.dev",
            "role": "admin",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


def public_jwk(public_key: RSAPublicKey, *, kid: str = "test-key") -> dict[str, str]:
    numbers = public_key.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": kid,
        "n": base64url_uint(numbers.n),
        "e": base64url_uint(numbers.e),
    }


def base64url_uint(value: int) -> str:
    data = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
