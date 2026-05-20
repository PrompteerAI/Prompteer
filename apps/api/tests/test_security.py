import base64
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from fastapi import HTTPException
from starlette.requests import Request

from app.api.deps import get_current_principal
from app.core.security import AuthTokenError, verify_jwt_with_jwks


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


def request_for_auth() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": []})


def sign_test_token(private_key: RSAPrivateKey) -> str:
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
        headers={"kid": "test-key"},
    )


def public_jwk(public_key: RSAPublicKey) -> dict[str, str]:
    numbers = public_key.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": "test-key",
        "n": base64url_uint(numbers.n),
        "e": base64url_uint(numbers.e),
    }


def base64url_uint(value: int) -> str:
    data = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
