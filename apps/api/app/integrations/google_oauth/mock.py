"""Local Google OpenID Connect/OAuth 2.0 mock.

Schema references verified on 2026-05-22:
- https://developers.google.com/identity/openid-connect/reference
- https://developers.google.com/identity/protocols/oauth2/web-server

The mock intentionally mirrors Google's endpoint paths so Auth.js can use it as a
normal OIDC issuer in local development when real Google credentials are absent.
"""

from __future__ import annotations

import base64
import os
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import gettempdir
from typing import Annotated, Any
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.feature_flags import dev_routes_enabled

MOCK_GOOGLE_CLIENT_ID = "mock-google-client"
MOCK_GOOGLE_CLIENT_SECRET = "mock-google-secret"
MOCK_GOOGLE_KEY_ID = "prompteer-dev-google-oauth"
MOCK_GOOGLE_TOKEN_SECRET = "prompteer-dev-google-oauth-state"
ACCESS_TOKEN_SECONDS = 3600
AUTH_CODE_SECONDS = 300
MOCK_GOOGLE_PRIVATE_KEY_PATH = (
    Path(gettempdir()) / "prompteer" / "mock-google-oauth-private-key.pem"
)
MOCK_GOOGLE_KEY_WAIT_ATTEMPTS = 40
MOCK_GOOGLE_KEY_WAIT_SECONDS = 0.05


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


def load_private_key_pem(private_key_pem: bytes, *, source: Path) -> RSAPrivateKey:
    loaded_private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(loaded_private_key, RSAPrivateKey):
        msg = f"Mock Google OAuth private key at {source} must be an RSA private key."
        raise TypeError(msg)
    return loaded_private_key


def serialize_private_key(private_key: RSAPrivateKey) -> bytes:
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def generate_private_key_file(path: Path) -> RSAPrivateKey:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key_pem = serialize_private_key(private_key)
    temp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    file_descriptor = os.open(temp_path, flags, 0o600)
    with os.fdopen(file_descriptor, "wb") as key_file:
        key_file.write(private_key_pem)
    temp_path.replace(path)
    with suppress(OSError):
        path.chmod(0o600)
    return private_key


def wait_for_private_key(path: Path) -> RSAPrivateKey:
    for _ in range(MOCK_GOOGLE_KEY_WAIT_ATTEMPTS):
        if path.exists():
            try:
                return load_private_key_pem(path.read_bytes(), source=path)
            except (OSError, TypeError, ValueError):
                time.sleep(MOCK_GOOGLE_KEY_WAIT_SECONDS)
                continue
        time.sleep(MOCK_GOOGLE_KEY_WAIT_SECONDS)
    msg = f"Mock Google OAuth private key was not created at {path}."
    raise RuntimeError(msg)


def load_or_create_private_key(path: Path = MOCK_GOOGLE_PRIVATE_KEY_PATH) -> RSAPrivateKey:
    if path.exists():
        return load_private_key_pem(path.read_bytes(), source=path)

    path.parent.mkdir(parents=True, exist_ok=True)
    with suppress(OSError):
        path.parent.chmod(0o700)

    lock_path = path.with_name(f"{path.name}.lock")
    try:
        file_descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return wait_for_private_key(path)

    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as lock_file:
            lock_file.write(str(os.getpid()))
        return generate_private_key_file(path)
    finally:
        with suppress(FileNotFoundError):
            lock_path.unlink()


DEV_PRIVATE_KEY: RSAPrivateKey = load_or_create_private_key()
DEV_PUBLIC_KEY: RSAPublicKey = DEV_PRIVATE_KEY.public_key()

router = APIRouter(tags=["mock-google-oauth"])


def issuer_url() -> str:
    return settings.auth_mock_google_issuer.rstrip("/")


def server_base_url() -> str:
    return (settings.auth_mock_google_server_base_url or issuer_url()).rstrip("/")


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


def encode_mock_state(payload: dict[str, Any], *, lifetime_seconds: int) -> str:
    now = datetime.now(tz=UTC)
    return str(
        jwt.encode(
            {
                **payload,
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(seconds=lifetime_seconds)).timestamp()),
            },
            MOCK_GOOGLE_TOKEN_SECRET,
            algorithm="HS256",
        )
    )


def decode_mock_state(
    token: str,
    *,
    expected_type: str,
    invalid_status_code: int,
    invalid_detail: str,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            MOCK_GOOGLE_TOKEN_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "mock_type"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=invalid_status_code, detail=invalid_detail) from exc
    if not isinstance(payload, dict) or payload.get("mock_type") != expected_type:
        raise HTTPException(status_code=invalid_status_code, detail=invalid_detail)
    return payload


def payload_str(payload: dict[str, Any], key: str, *, detail: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    return value


def encode_authorization_code(authorization_code: AuthorizationCode) -> str:
    payload: dict[str, Any] = {
        "mock_type": "authorization_code",
        "email": authorization_code.email,
        "client_id": authorization_code.client_id,
        "redirect_uri": authorization_code.redirect_uri,
        "scope": authorization_code.scope,
    }
    if authorization_code.nonce is not None:
        payload["nonce"] = authorization_code.nonce
    return encode_mock_state(payload, lifetime_seconds=AUTH_CODE_SECONDS)


def decode_authorization_code(code: str) -> AuthorizationCode:
    payload = decode_mock_state(
        code,
        expected_type="authorization_code",
        invalid_status_code=status.HTTP_400_BAD_REQUEST,
        invalid_detail="Invalid code.",
    )
    email = payload_str(payload, "email", detail="Invalid code.")
    if email not in MOCK_USERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code.")
    nonce = payload.get("nonce")
    if nonce is not None and not isinstance(nonce, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code.")
    return AuthorizationCode(
        email=email,
        client_id=payload_str(payload, "client_id", detail="Invalid code."),
        redirect_uri=payload_str(payload, "redirect_uri", detail="Invalid code."),
        scope=payload_str(payload, "scope", detail="Invalid code."),
        nonce=nonce,
    )


def issue_access_token(user: MockGoogleUser) -> str:
    return "ya29." + encode_mock_state(
        {"mock_type": "access_token", "email": user.email},
        lifetime_seconds=ACCESS_TOKEN_SECONDS,
    )


def access_token_email(access_token: str) -> str:
    if not access_token.startswith("ya29."):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token."
        )
    payload = decode_mock_state(
        access_token.removeprefix("ya29."),
        expected_type="access_token",
        invalid_status_code=status.HTTP_401_UNAUTHORIZED,
        invalid_detail="Invalid access token.",
    )
    email = payload.get("email")
    if not isinstance(email, str) or email not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token."
        )
    return email


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
    server_base = server_base_url()
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/o/oauth2/v2/auth",
        "token_endpoint": f"{server_base}/token",
        "userinfo_endpoint": f"{server_base}/v3/userinfo",
        "jwks_uri": f"{server_base}/oauth2/v3/certs",
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
    code = encode_authorization_code(
        AuthorizationCode(
            email=user.email,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            nonce=nonce,
        )
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
    authorization_code = decode_authorization_code(code)
    if not redirect_uris_match(authorization_code.redirect_uri, redirect_uri):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri.",
        )
    if authorization_code.client_id != authenticated_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client_id.")
    user = MOCK_USERS[authorization_code.email]
    access_token = issue_access_token(user)
    return {
        "access_token": access_token,
        "expires_in": ACCESS_TOKEN_SECONDS,
        "refresh_token": "1//"
        + encode_mock_state(
            {"mock_type": "refresh_token", "email": user.email},
            lifetime_seconds=ACCESS_TOKEN_SECONDS,
        ),
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
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )
    return userinfo_payload(MOCK_USERS[access_token_email(access_token)])


@router.get("/oauth2/v3/certs")
async def jwks() -> dict[str, list[dict[str, str]]]:
    require_mock_enabled()
    return {"keys": [public_jwk()]}


def authorization_header(client_id: str, client_secret: str) -> str:
    credential = f"{quote(client_id)}:{quote(client_secret)}"
    encoded = base64.b64encode(credential.encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"
