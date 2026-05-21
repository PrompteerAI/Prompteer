"""Tests for Auth.js-issued API bearer token verification."""

import base64
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from fastapi import HTTPException
from starlette.requests import Request

from app.api.deps import get_current_principal
from app.core import security
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
