"""JWT principal validation against Auth.js-issued RS256 API tokens."""

import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import Any

import httpx
import jwt

from app.core.config import settings

JWKS_CACHE_SECONDS = 300.0
JWKS_FETCH_ATTEMPTS = 2
JWKS_FETCH_TIMEOUT_SECONDS = 5.0
NO_MATCHING_KID_ERROR = "No JWKS key matched the JWT kid."


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str | None = None
    is_admin: bool = False


class AuthTokenError(ValueError):
    pass


@dataclass(frozen=True)
class JwksCacheEntry:
    url: str
    expires_at: float
    jwks: dict[str, Any]


_jwks_cache: JwksCacheEntry | None = None


async def verify_bearer_token(token: str) -> Principal:
    try:
        return verify_jwt_with_jwks(
            token,
            await get_cached_jwks(settings.auth_jwks_url),
            issuer=settings.auth_jwt_issuer.rstrip("/"),
            audience=settings.auth_jwt_audience,
        )
    except AuthTokenError as exc:
        if str(exc) != NO_MATCHING_KID_ERROR:
            raise
    return verify_jwt_with_jwks(
        token,
        await get_cached_jwks(settings.auth_jwks_url, force_refresh=True),
        issuer=settings.auth_jwt_issuer.rstrip("/"),
        audience=settings.auth_jwt_audience,
    )


async def get_cached_jwks(jwks_url: str, *, force_refresh: bool = False) -> dict[str, Any]:
    global _jwks_cache
    if (
        not force_refresh
        and _jwks_cache is not None
        and _jwks_cache.url == jwks_url
        and _jwks_cache.expires_at > monotonic()
    ):
        return _jwks_cache.jwks

    jwks = await fetch_jwks(jwks_url)
    _jwks_cache = JwksCacheEntry(
        url=jwks_url,
        expires_at=monotonic() + JWKS_CACHE_SECONDS,
        jwks=jwks,
    )
    return jwks


def clear_jwks_cache() -> None:
    global _jwks_cache
    _jwks_cache = None


async def fetch_jwks(jwks_url: str) -> dict[str, Any]:
    body: Any = None
    for attempt in range(1, JWKS_FETCH_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=JWKS_FETCH_TIMEOUT_SECONDS) as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
                body = response.json()
        except httpx.TransportError as exc:
            if attempt < JWKS_FETCH_ATTEMPTS:
                await asyncio.sleep(0.2 * attempt)
                continue
            raise AuthTokenError("JWKS endpoint was unreachable.") from exc
        except httpx.HTTPStatusError as exc:
            raise AuthTokenError("JWKS endpoint returned an error.") from exc
        break
    if not isinstance(body, dict) or not isinstance(body.get("keys"), list):
        raise AuthTokenError("JWKS endpoint did not return a key set.")
    return body


def verify_jwt_with_jwks(
    token: str,
    jwks: dict[str, Any],
    *,
    issuer: str,
    audience: str,
) -> Principal:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise AuthTokenError("Invalid JWT header.") from exc
    kid = header.get("kid")
    key_data = find_jwk(jwks, kid)
    try:
        public_key = jwt.PyJWK.from_dict(key_data).key
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise AuthTokenError("Invalid Auth.js JWT.") from exc
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AuthTokenError("JWT is missing subject.")
    email = claims.get("email")
    role = claims.get("role")
    return Principal(
        subject=subject,
        email=email if isinstance(email, str) else None,
        is_admin=role == "admin",
    )


def find_jwk(jwks: dict[str, Any], kid: Any) -> dict[str, Any]:
    keys = jwks.get("keys")
    if not isinstance(keys, list):
        raise AuthTokenError("JWKS endpoint did not return keys[].")
    for key in keys:
        if isinstance(key, dict) and key.get("kid") == kid:
            return key
    raise AuthTokenError(NO_MATCHING_KID_ERROR)
