"""JWT principal validation against Auth.js-issued RS256 API tokens."""

import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import Any

import httpx
import jwt

from app.core.config import settings

JWKS_CACHE_SECONDS = 300.0
JWKS_UNKNOWN_KID_REFRESH_BACKOFF_SECONDS = 5.0
JWKS_FETCH_ATTEMPTS = 2
JWKS_FETCH_TIMEOUT_SECONDS = 5.0
NO_MATCHING_KID_ERROR = "No JWKS key matched the JWT kid."
SIGNATURE_MISMATCH_ERROR = "JWT signature did not match the JWKS key."


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str | None = None
    is_admin: bool = False


class AuthTokenError(ValueError):
    pass


class JwksNoMatchingKidError(AuthTokenError):
    pass


class JwksSignatureMismatchError(AuthTokenError):
    pass


@dataclass(frozen=True)
class JwksCacheEntry:
    url: str
    expires_at: float
    jwks: dict[str, Any]


_jwks_cache: JwksCacheEntry | None = None
_last_unknown_kid_refresh_at: dict[str, float] = {}


async def verify_bearer_token(token: str) -> Principal:
    jwks_url = settings.auth_jwks_url
    issuer = settings.auth_jwt_issuer.rstrip("/")
    audience = settings.auth_jwt_audience
    jwks_was_cached = has_valid_cached_jwks(jwks_url)
    try:
        return verify_jwt_with_jwks(
            token,
            await get_cached_jwks(jwks_url),
            issuer=issuer,
            audience=audience,
        )
    except JwksNoMatchingKidError:
        if not should_refresh_unknown_kid(jwks_url):
            raise
    except JwksSignatureMismatchError:
        if not jwks_was_cached or not should_refresh_signature_mismatch():
            raise
    return verify_jwt_with_jwks(
        token,
        await get_cached_jwks(jwks_url, force_refresh=True),
        issuer=issuer,
        audience=audience,
    )


def has_valid_cached_jwks(jwks_url: str) -> bool:
    return get_valid_cached_jwks(jwks_url) is not None


def get_valid_cached_jwks(jwks_url: str) -> dict[str, Any] | None:
    cache = _jwks_cache
    if cache is None or cache.url != jwks_url or cache.expires_at <= monotonic():
        return None
    return cache.jwks


async def get_cached_jwks(jwks_url: str, *, force_refresh: bool = False) -> dict[str, Any]:
    global _jwks_cache
    cached_jwks = get_valid_cached_jwks(jwks_url)
    if not force_refresh and cached_jwks is not None:
        return cached_jwks

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
    _last_unknown_kid_refresh_at.clear()


def should_refresh_unknown_kid(jwks_url: str) -> bool:
    now = monotonic()
    last_refresh_at = _last_unknown_kid_refresh_at.get(jwks_url)
    if (
        last_refresh_at is not None
        and now - last_refresh_at < JWKS_UNKNOWN_KID_REFRESH_BACKOFF_SECONDS
    ):
        return False
    _last_unknown_kid_refresh_at[jwks_url] = now
    return True


def should_refresh_signature_mismatch() -> bool:
    return settings.is_development


async def fetch_jwks(jwks_url: str) -> dict[str, Any]:
    body: Any = None
    for attempt in range(1, JWKS_FETCH_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=JWKS_FETCH_TIMEOUT_SECONDS) as client:
                response = await client.get(jwks_url)
                response.raise_for_status()
                try:
                    body = response.json()
                except ValueError as exc:
                    raise AuthTokenError("JWKS endpoint returned invalid JSON.") from exc
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
    except jwt.InvalidSignatureError as exc:
        raise JwksSignatureMismatchError(SIGNATURE_MISMATCH_ERROR) from exc
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
    raise JwksNoMatchingKidError(NO_MATCHING_KID_ERROR)
