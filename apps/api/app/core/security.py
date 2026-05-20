"""JWT principal validation against Auth.js-issued RS256 API tokens."""

from dataclasses import dataclass
from typing import Any

import httpx
import jwt

from app.core.config import settings


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str | None = None
    is_admin: bool = False


class AuthTokenError(ValueError):
    pass


async def verify_bearer_token(token: str) -> Principal:
    jwks = await fetch_jwks(settings.auth_jwks_url)
    return verify_jwt_with_jwks(
        token,
        jwks,
        issuer=settings.auth_jwt_issuer.rstrip("/"),
        audience=settings.auth_jwt_audience,
    )


async def fetch_jwks(jwks_url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        body = response.json()
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
    raise AuthTokenError("No JWKS key matched the JWT kid.")
