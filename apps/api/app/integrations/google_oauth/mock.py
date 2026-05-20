"""Local Google OpenID Connect/OAuth 2.0 mock.

Schema references verified on 2026-05-20:
- https://developers.google.com/identity/openid-connect/openid-connect
- https://developers.google.com/identity/protocols/oauth2/web-server

The mock intentionally mirrors Google's endpoint paths so Auth.js can use it as a
normal OIDC issuer in local development when real Google credentials are absent.
"""

from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.feature_flags import dev_routes_enabled

MOCK_GOOGLE_CLIENT_ID = "mock-google-client"
MOCK_GOOGLE_CLIENT_SECRET = "mock-google-secret"
MOCK_GOOGLE_KEY_ID = "prompteer-dev-google-oauth"
ACCESS_TOKEN_SECONDS = 3600


@dataclass(frozen=True)
class MockGoogleUser:
    sub: str
    email: str
    name: str
    given_name: str
    family_name: str
    picture: str
    locale: str = "en"
    email_verified: bool = True


@dataclass(frozen=True)
class AuthorizationCode:
    email: str
    client_id: str
    redirect_uri: str
    scope: str
    nonce: str | None


MOCK_USERS: dict[str, MockGoogleUser] = {
    "admin@prompteer.dev": MockGoogleUser(
        sub="mock-google-oauth2|admin",
        email="admin@prompteer.dev",
        name="Prompteer Admin",
        given_name="Prompteer",
        family_name="Admin",
        picture="https://prompteer.dev/mock-avatars/admin.png",
    ),
    "paid@prompteer.dev": MockGoogleUser(
        sub="mock-google-oauth2|paid",
        email="paid@prompteer.dev",
        name="Paid Prompt Engineer",
        given_name="Paid",
        family_name="Engineer",
        picture="https://prompteer.dev/mock-avatars/paid.png",
    ),
    "free@prompteer.dev": MockGoogleUser(
        sub="mock-google-oauth2|free",
        email="free@prompteer.dev",
        name="Free Prompt Builder",
        given_name="Free",
        family_name="Builder",
        picture="https://prompteer.dev/mock-avatars/free.png",
    ),
}

DEFAULT_MOCK_EMAIL = "free@prompteer.dev"

DEV_PRIVATE_KEY: RSAPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
DEV_PUBLIC_KEY: RSAPublicKey = DEV_PRIVATE_KEY.public_key()

AUTH_CODES: dict[str, AuthorizationCode] = {}
ACCESS_TOKENS: dict[str, str] = {}

router = APIRouter(tags=["mock-google-oauth"])


def issuer_url() -> str:
    return settings.auth_mock_google_issuer.rstrip("/")


def require_mock_enabled() -> None:
    if settings.google_client_id and settings.google_client_secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not dev_routes_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def base64url_uint(value: int) -> str:
    length = max(1, (value.bit_length() + 7) // 8)
    data = value.to_bytes(length, "big")
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def public_jwk() -> dict[str, str]:
    numbers = DEV_PUBLIC_KEY.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": MOCK_GOOGLE_KEY_ID,
        "n": base64url_uint(numbers.n),
        "e": base64url_uint(numbers.e),
    }


def userinfo_payload(user: MockGoogleUser) -> dict[str, str | bool]:
    return {
        "sub": user.sub,
        "email": user.email,
        "email_verified": user.email_verified,
        "name": user.name,
        "given_name": user.given_name,
        "family_name": user.family_name,
        "picture": user.picture,
        "locale": user.locale,
    }


def select_user(login_hint: str | None) -> MockGoogleUser:
    if login_hint and login_hint in MOCK_USERS:
        return MOCK_USERS[login_hint]
    return MOCK_USERS[DEFAULT_MOCK_EMAIL]


def append_query_params(url: str, params: dict[str, str]) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(params)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def redirect_uris_match(expected: str, actual: str) -> bool:
    if expected == actual:
        return True
    expected_parts = urlsplit(expected)
    actual_parts = urlsplit(actual)
    loopback_hosts = {"127.0.0.1", "localhost"}
    return (
        expected_parts.scheme == actual_parts.scheme
        and expected_parts.hostname in loopback_hosts
        and actual_parts.hostname in loopback_hosts
        and (expected_parts.port or default_port(expected_parts.scheme))
        == (actual_parts.port or default_port(actual_parts.scheme))
        and expected_parts.path == actual_parts.path
        and expected_parts.query == actual_parts.query
        and expected_parts.fragment == actual_parts.fragment
    )


def default_port(scheme: str) -> int | None:
    if scheme == "http":
        return 80
    if scheme == "https":
        return 443
    return None


def decode_basic_client_credentials(request: Request) -> tuple[str | None, str | None]:
    authorization = request.headers.get("authorization", "")
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "basic" or not credentials:
        return None, None
    try:
        decoded = base64.b64decode(credentials).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client authentication.",
        ) from exc
    client_id, separator, client_secret = decoded.partition(":")
    if separator == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client authentication.",
        )
    return client_id, client_secret


def validate_client(
    request: Request,
    form_client_id: str | None,
    form_client_secret: str | None,
) -> str:
    basic_client_id, basic_client_secret = decode_basic_client_credentials(request)
    client_id = form_client_id or basic_client_id
    client_secret = form_client_secret or basic_client_secret
    if client_id != MOCK_GOOGLE_CLIENT_ID or client_secret != MOCK_GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client authentication.",
        )
    return client_id


def sign_id_token(*, user: MockGoogleUser, client_id: str, nonce: str | None) -> str:
    now = datetime.now(tz=UTC)
    payload: dict[str, Any] = {
        "iss": issuer_url(),
        "aud": client_id,
        "azp": client_id,
        "sub": user.sub,
        "email": user.email,
        "email_verified": user.email_verified,
        "name": user.name,
        "picture": user.picture,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ACCESS_TOKEN_SECONDS)).timestamp()),
    }
    if nonce is not None:
        payload["nonce"] = nonce
    token = jwt.encode(
        payload,
        DEV_PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": MOCK_GOOGLE_KEY_ID},
    )
    return str(token)


@router.get("/.well-known/openid-configuration")
async def openid_configuration() -> dict[str, object]:
    require_mock_enabled()
    issuer = issuer_url()
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/o/oauth2/v2/auth",
        "token_endpoint": f"{issuer}/token",
        "userinfo_endpoint": f"{issuer}/v3/userinfo",
        "jwks_uri": f"{issuer}/oauth2/v3/certs",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "email", "profile"],
        "claims_supported": [
            "aud",
            "azp",
            "email",
            "email_verified",
            "exp",
            "family_name",
            "given_name",
            "iat",
            "iss",
            "locale",
            "name",
            "picture",
            "sub",
        ],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
    }


@router.get("/o/oauth2/v2/auth")
async def authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: str = "openid email profile",
    state: str | None = None,
    login_hint: str | None = None,
    nonce: str | None = None,
) -> RedirectResponse:
    require_mock_enabled()
    if client_id != MOCK_GOOGLE_CLIENT_ID or response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth authorization request.",
        )
    user = select_user(login_hint)
    code = secrets.token_urlsafe(32)
    AUTH_CODES[code] = AuthorizationCode(
        email=user.email,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        nonce=nonce,
    )
    query = {"code": code}
    if state is not None:
        query["state"] = state
    return RedirectResponse(append_query_params(redirect_uri, query), status_code=302)


@router.post("/token")
async def token(
    request: Request,
    grant_type: Annotated[str, Form()],
    code: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form()],
    client_id: Annotated[str | None, Form()] = None,
    client_secret: Annotated[str | None, Form()] = None,
) -> dict[str, str | int]:
    require_mock_enabled()
    authenticated_client_id = validate_client(request, client_id, client_secret)
    if grant_type != "authorization_code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported grant_type.",
        )
    authorization_code = AUTH_CODES.pop(code, None)
    if authorization_code is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code.")
    if not redirect_uris_match(authorization_code.redirect_uri, redirect_uri):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri.",
        )
    if authorization_code.client_id != authenticated_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client_id.")
    user = MOCK_USERS[authorization_code.email]
    access_token = f"ya29.{secrets.token_urlsafe(32)}"
    ACCESS_TOKENS[access_token] = user.email
    return {
        "access_token": access_token,
        "expires_in": ACCESS_TOKEN_SECONDS,
        "refresh_token": f"1//{secrets.token_urlsafe(32)}",
        "scope": authorization_code.scope,
        "token_type": "Bearer",
        "id_token": sign_id_token(
            user=user,
            client_id=authenticated_client_id,
            nonce=authorization_code.nonce,
        ),
    }


@router.get("/v3/userinfo")
async def userinfo(request: Request) -> dict[str, str | bool]:
    require_mock_enabled()
    authorization = request.headers.get("authorization", "")
    scheme, _, access_token = authorization.partition(" ")
    if scheme.lower() != "bearer" or access_token not in ACCESS_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )
    return userinfo_payload(MOCK_USERS[ACCESS_TOKENS[access_token]])


@router.get("/oauth2/v3/certs")
async def jwks() -> dict[str, list[dict[str, str]]]:
    require_mock_enabled()
    return {"keys": [public_jwk()]}


def authorization_header(client_id: str, client_secret: str) -> str:
    credential = f"{quote(client_id)}:{quote(client_secret)}"
    encoded = base64.b64encode(credential.encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"
