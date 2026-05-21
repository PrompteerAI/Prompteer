"""Tests for the local Google-compatible OIDC mock and discovery metadata."""

from typing import Any, cast
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.integrations.google_oauth.mock import (
    DEV_PUBLIC_KEY,
    MOCK_GOOGLE_CLIENT_ID,
    MOCK_GOOGLE_CLIENT_SECRET,
    authorization_header,
)
from app.main import create_app


@pytest.fixture(autouse=True)
def enable_mock_google(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "env", "development")
    monkeypatch.setattr(settings, "enable_dev_routes", True)
    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "google_client_secret", "")
    monkeypatch.setattr(settings, "auth_mock_google_issuer", "http://localhost:8000")
    monkeypatch.setattr(settings, "auth_mock_google_server_base_url", "")


def test_openid_discovery_and_jwks_shape() -> None:
    client = TestClient(create_app())

    discovery_response = client.get("/.well-known/openid-configuration")
    assert discovery_response.status_code == 200
    discovery = cast(dict[str, Any], discovery_response.json())
    assert discovery["issuer"] == "http://localhost:8000"
    assert discovery["authorization_endpoint"] == "http://localhost:8000/o/oauth2/v2/auth"
    assert discovery["token_endpoint"] == "http://localhost:8000/token"
    assert discovery["userinfo_endpoint"] == "http://localhost:8000/v3/userinfo"
    assert discovery["jwks_uri"] == "http://localhost:8000/oauth2/v3/certs"

    jwks_response = client.get("/oauth2/v3/certs")
    assert jwks_response.status_code == 200
    jwks = cast(dict[str, Any], jwks_response.json())
    key = cast(dict[str, str], jwks["keys"][0])
    assert key["kty"] == "RSA"
    assert key["alg"] == "RS256"
    assert key["use"] == "sig"


def test_openid_discovery_can_publish_internal_server_endpoints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "auth_mock_google_issuer", "http://localhost")
    monkeypatch.setattr(settings, "auth_mock_google_server_base_url", "http://api:8000")
    client = TestClient(create_app())

    discovery_response = client.get("/.well-known/openid-configuration")

    assert discovery_response.status_code == 200
    discovery = cast(dict[str, Any], discovery_response.json())
    assert discovery["issuer"] == "http://localhost"
    assert discovery["authorization_endpoint"] == "http://localhost/o/oauth2/v2/auth"
    assert discovery["token_endpoint"] == "http://api:8000/token"
    assert discovery["userinfo_endpoint"] == "http://api:8000/v3/userinfo"
    assert discovery["jwks_uri"] == "http://api:8000/oauth2/v3/certs"


def test_mock_google_authorization_code_flow() -> None:
    client = TestClient(create_app())
    redirect_uri = "http://localhost:3000/api/auth/callback/google"

    authorization_response = client.get(
        "/o/oauth2/v2/auth",
        params={
            "client_id": MOCK_GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": "opaque-state",
            "login_hint": "admin@prompteer.dev",
            "nonce": "nonce-value",
        },
        follow_redirects=False,
    )
    assert authorization_response.status_code == 302
    location = authorization_response.headers["location"]
    redirect_query = parse_qs(urlparse(location).query)
    code = redirect_query["code"][0]
    assert redirect_query["state"] == ["opaque-state"]

    token_response = client.post(
        "/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
        headers={
            "Authorization": authorization_header(
                MOCK_GOOGLE_CLIENT_ID,
                MOCK_GOOGLE_CLIENT_SECRET,
            )
        },
    )
    assert token_response.status_code == 200
    token_body = cast(dict[str, Any], token_response.json())
    assert token_body["token_type"] == "Bearer"
    assert token_body["expires_in"] == 3600
    assert token_body["scope"] == "openid email profile"
    assert str(token_body["access_token"]).startswith("ya29.")
    assert str(token_body["refresh_token"]).startswith("1//")

    claims = jwt.decode(
        cast(str, token_body["id_token"]),
        DEV_PUBLIC_KEY,
        algorithms=["RS256"],
        audience=MOCK_GOOGLE_CLIENT_ID,
        issuer=settings.auth_mock_google_issuer,
    )
    assert claims["sub"] == "mock-google-oauth2|admin"
    assert claims["email"] == "admin@prompteer.dev"
    assert claims["nonce"] == "nonce-value"

    userinfo_response = client.get(
        "/v3/userinfo",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )
    assert userinfo_response.status_code == 200
    profile = cast(dict[str, Any], userinfo_response.json())
    assert profile == {
        "sub": "mock-google-oauth2|admin",
        "email": "admin@prompteer.dev",
        "email_verified": True,
        "name": "Prompteer Admin",
        "given_name": "Prompteer",
        "family_name": "Admin",
        "picture": "https://prompteer.dev/mock-avatars/admin.png",
        "locale": "en",
    }
