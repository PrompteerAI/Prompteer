"""API v1 health probe routes; no sibling health API version exists yet."""

import asyncio
from collections.abc import Awaitable, Mapping
from typing import Any, Literal, TypedDict, cast
from urllib.parse import quote

import httpx
from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from app.core.bootstrap import integration_modes
from app.core.config import settings
from app.core.feature_flags import dev_routes_enabled, feature_flags
from app.core.migrations import MigrationState, migration_state
from app.db.session import engine
from app.integrations.http import RetryPolicy
from app.integrations.http import request as outbound_request

router = APIRouter(prefix="/health", tags=["health"])

HealthStatus = Literal["ok", "fail", "disabled"]
GOOGLE_OIDC_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
STRIPE_BASE_URL = "https://api.stripe.com"
SENDGRID_BASE_URL = "https://api.sendgrid.com"
PROVIDER_READINESS_TIMEOUT_SECONDS = 2.0
PROVIDER_READINESS_RETRY = RetryPolicy(max_attempts=1, base_delay_seconds=0, jitter_seconds=0)


class IntegrationCheck(TypedDict):
    status: HealthStatus
    mode: str
    detail: str


class DependencyCheck(TypedDict):
    status: Literal["ok", "fail"]
    detail: str


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


async def check_database() -> DependencyCheck:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return {
            "status": "fail",
            "detail": f"database query failed: {type(exc).__name__}.",
        }
    return {"status": "ok", "detail": "database query succeeded."}


async def check_redis() -> DependencyCheck:
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    try:
        await cast(Awaitable[bool], client.ping())
    except Exception as exc:
        return {
            "status": "fail",
            "detail": f"Redis ping failed: {type(exc).__name__}.",
        }
    finally:
        await client.aclose()
    return {"status": "ok", "detail": "Redis ping succeeded."}


async def check_integrations() -> dict[str, IntegrationCheck]:
    modes = integration_modes()
    flags = feature_flags()
    google_oauth, llm, stripe, email = await asyncio.gather(
        check_google_oauth(mode=modes["google_oauth"]),
        check_llm_integration(
            feature_enabled=flags["llm"],
            mode=modes["llm"],
            mock_detail="deterministic LLM mock client is selected",
        ),
        check_stripe_integration(
            feature_enabled=flags["payments"],
            mode=modes["stripe"],
            mock_detail="local Stripe mock checkout is selected",
        ),
        check_email_integration(
            feature_enabled=flags["email"],
            mode=modes["email"],
            mock_detail="local SendGrid mock mailbox is selected",
        ),
    )
    return {
        "google_oauth": google_oauth,
        "llm": llm,
        "stripe": stripe,
        "email": email,
    }


async def check_google_oauth(*, mode: str) -> IntegrationCheck:
    if bool(settings.google_client_id) != bool(settings.google_client_secret):
        return {
            "status": "fail",
            "mode": "partial",
            "detail": "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set together.",
        }
    if mode == "real":
        return await check_google_oidc_reachable(mode=mode)
    if dev_routes_enabled():
        return {
            "status": "ok",
            "mode": mode,
            "detail": "local Google OIDC mock routes are available",
        }
    return {
        "status": "fail",
        "mode": mode,
        "detail": "mock Google OAuth requires dev routes or real Google credentials.",
    }


async def check_llm_integration(
    *,
    feature_enabled: bool,
    mode: str,
    mock_detail: str,
) -> IntegrationCheck:
    base_check = check_featured_integration_base(
        feature_enabled=feature_enabled,
        mode=mode,
        mock_detail=mock_detail,
    )
    if base_check is not None:
        return base_check
    if settings.openai_api_key:
        return await check_openai_reachable(mode=mode)
    if settings.anthropic_api_key:
        return await check_anthropic_reachable(mode=mode)
    return integration_fail(
        mode=mode,
        detail="real LLM mode selected without provider credentials.",
    )


async def check_stripe_integration(
    *,
    feature_enabled: bool,
    mode: str,
    mock_detail: str,
) -> IntegrationCheck:
    base_check = check_featured_integration_base(
        feature_enabled=feature_enabled,
        mode=mode,
        mock_detail=mock_detail,
    )
    if base_check is not None:
        return base_check
    if not settings.stripe_secret_key:
        return integration_fail(
            mode=mode,
            detail="real Stripe mode selected without STRIPE_SECRET_KEY.",
        )
    if not settings.stripe_webhook_secret:
        stripe_check = await check_stripe_reachable(mode=mode)
        if stripe_check["status"] != "ok":
            return stripe_check
        webhook_detail = (
            "Stripe balance endpoint is reachable; STRIPE_WEBHOOK_SECRET is not set, "
            "so live webhook fulfillment will reject events until configured."
        )
        if settings.is_production:
            return integration_fail(mode=mode, detail=webhook_detail)
        return integration_ok(mode=mode, detail=webhook_detail)
    return await check_stripe_reachable(mode=mode)


async def check_email_integration(
    *,
    feature_enabled: bool,
    mode: str,
    mock_detail: str,
) -> IntegrationCheck:
    base_check = check_featured_integration_base(
        feature_enabled=feature_enabled,
        mode=mode,
        mock_detail=mock_detail,
    )
    if base_check is not None:
        return base_check
    return await check_sendgrid_reachable(mode=mode)


def check_featured_integration_base(
    *,
    feature_enabled: bool,
    mode: str,
    mock_detail: str,
) -> IntegrationCheck | None:
    if not feature_enabled:
        return {"status": "disabled", "mode": mode, "detail": "feature flag is disabled"}
    if mode == "real":
        return None
    if dev_routes_enabled():
        return {"status": "ok", "mode": mode, "detail": mock_detail}
    return {
        "status": "fail",
        "mode": mode,
        "detail": "mock mode requires dev routes or real provider credentials.",
    }


async def check_google_oidc_reachable(*, mode: str) -> IntegrationCheck:
    try:
        discovery_response = await provider_readiness_request(
            provider="google_oauth",
            method="GET",
            url=GOOGLE_OIDC_DISCOVERY_URL,
            headers={"accept": "application/json"},
        )
        if not response_succeeded(discovery_response):
            return integration_fail(
                mode=mode,
                detail=(f"Google OIDC discovery returned HTTP {discovery_response.status_code}."),
            )
        discovery = response_json_object(discovery_response)
        if discovery is None:
            return integration_fail(
                mode=mode,
                detail="Google OIDC discovery returned an unexpected response shape.",
            )
        jwks_uri = discovery.get("jwks_uri")
        if not isinstance(jwks_uri, str) or not jwks_uri:
            return integration_fail(mode=mode, detail="Google OIDC discovery missing jwks_uri.")

        jwks_response = await provider_readiness_request(
            provider="google_oauth",
            method="GET",
            url=jwks_uri,
            headers={"accept": "application/json"},
        )
        if not response_succeeded(jwks_response):
            return integration_fail(
                mode=mode,
                detail=f"Google JWKS endpoint returned HTTP {jwks_response.status_code}.",
            )
        jwks = response_json_object(jwks_response)
        if jwks is None:
            return integration_fail(
                mode=mode,
                detail="Google JWKS endpoint returned an unexpected response shape.",
            )
        keys = jwks.get("keys")
        if not isinstance(keys, list):
            return integration_fail(
                mode=mode,
                detail="Google JWKS endpoint returned an unexpected response shape.",
            )
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        return integration_fail(
            mode=mode,
            detail=f"Google OIDC readiness probe failed: {type(exc).__name__}.",
        )
    return integration_ok(mode=mode, detail="Google OIDC discovery and JWKS are reachable.")


async def check_openai_reachable(*, mode: str) -> IntegrationCheck:
    model = quote(settings.openai_chat_model, safe="")
    try:
        response = await provider_readiness_request(
            provider="openai",
            method="GET",
            url=f"{settings.openai_base_url.rstrip('/')}/models/{model}",
            headers={
                "authorization": f"Bearer {settings.openai_api_key}",
                "accept": "application/json",
            },
        )
        if not response_succeeded(response):
            return integration_fail(
                mode=mode,
                detail=f"OpenAI model probe returned HTTP {response.status_code}.",
            )
        body = response_json_object(response)
        if body is None:
            return integration_fail(
                mode=mode,
                detail="OpenAI model probe returned an unexpected response shape.",
            )
        if body.get("id") != settings.openai_chat_model or body.get("object") != "model":
            return integration_fail(
                mode=mode,
                detail="OpenAI model probe returned an unexpected response shape.",
            )
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        return integration_fail(
            mode=mode,
            detail=f"OpenAI readiness probe failed: {type(exc).__name__}.",
        )
    return integration_ok(mode=mode, detail="OpenAI model endpoint is reachable.")


async def check_anthropic_reachable(*, mode: str) -> IntegrationCheck:
    try:
        response = await provider_readiness_request(
            provider="anthropic",
            method="POST",
            url=f"{settings.anthropic_base_url.rstrip('/')}/messages/count_tokens",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": settings.anthropic_version,
                "content-type": "application/json",
                "accept": "application/json",
            },
            json_body={
                "model": settings.anthropic_model,
                "messages": [{"role": "user", "content": "ready"}],
            },
            request_body_for_logs={"model": settings.anthropic_model, "messages": "[redacted]"},
        )
        if not response_succeeded(response):
            return integration_fail(
                mode=mode,
                detail=f"Anthropic token-count probe returned HTTP {response.status_code}.",
            )
        body = response_json_object(response)
        if body is None:
            return integration_fail(
                mode=mode,
                detail="Anthropic token-count probe returned an unexpected response shape.",
            )
        if not isinstance(body.get("input_tokens"), int):
            return integration_fail(
                mode=mode,
                detail="Anthropic token-count probe returned an unexpected response shape.",
            )
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        return integration_fail(
            mode=mode,
            detail=f"Anthropic readiness probe failed: {type(exc).__name__}.",
        )
    return integration_ok(mode=mode, detail="Anthropic token-count endpoint is reachable.")


async def check_stripe_reachable(*, mode: str) -> IntegrationCheck:
    try:
        response = await provider_readiness_request(
            provider="stripe",
            method="GET",
            url=f"{STRIPE_BASE_URL}/v1/balance",
            headers={
                "authorization": f"Bearer {settings.stripe_secret_key}",
                "accept": "application/json",
            },
        )
        if not response_succeeded(response):
            return integration_fail(
                mode=mode,
                detail=f"Stripe balance probe returned HTTP {response.status_code}.",
            )
        body = response_json_object(response)
        if body is None:
            return integration_fail(
                mode=mode,
                detail="Stripe balance probe returned an unexpected response shape.",
            )
        if not isinstance(body.get("available"), list) or not isinstance(body.get("pending"), list):
            return integration_fail(
                mode=mode,
                detail="Stripe balance probe returned an unexpected response shape.",
            )
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        return integration_fail(
            mode=mode,
            detail=f"Stripe readiness probe failed: {type(exc).__name__}.",
        )
    return integration_ok(mode=mode, detail="Stripe balance endpoint is reachable.")


async def check_sendgrid_reachable(*, mode: str) -> IntegrationCheck:
    try:
        response = await provider_readiness_request(
            provider="sendgrid",
            method="GET",
            url=f"{SENDGRID_BASE_URL}/v3/scopes",
            headers={
                "authorization": f"Bearer {settings.sendgrid_api_key}",
                "accept": "application/json",
            },
        )
        if not response_succeeded(response):
            return integration_fail(
                mode=mode,
                detail=f"SendGrid scopes probe returned HTTP {response.status_code}.",
            )
        body = response_json_object(response)
        if body is None:
            return integration_fail(
                mode=mode,
                detail="SendGrid scopes probe returned an unexpected response shape.",
            )
        scopes = body.get("scopes")
        if not isinstance(scopes, list) or "mail.send" not in scopes:
            return integration_fail(
                mode=mode,
                detail="SendGrid API key does not expose the required mail.send scope.",
            )
    except (httpx.HTTPError, TypeError, ValueError) as exc:
        return integration_fail(
            mode=mode,
            detail=f"SendGrid readiness probe failed: {type(exc).__name__}.",
        )
    return integration_ok(mode=mode, detail="SendGrid scopes endpoint is reachable.")


async def provider_readiness_request(
    *,
    provider: str,
    method: str,
    url: str,
    headers: Mapping[str, str],
    json_body: object | None = None,
    request_body_for_logs: object | None = None,
) -> httpx.Response:
    return await outbound_request(
        provider=provider,
        method=method,
        url=url,
        timeout_seconds=PROVIDER_READINESS_TIMEOUT_SECONDS,
        headers=headers,
        json_body=json_body,
        request_body_for_logs=request_body_for_logs,
        retry_policy=PROVIDER_READINESS_RETRY,
    )


def response_succeeded(response: httpx.Response) -> bool:
    return 200 <= response.status_code < 300


def response_json_object(response: httpx.Response) -> dict[str, Any] | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, dict):
        return None
    return body


def integration_ok(*, mode: str, detail: str) -> IntegrationCheck:
    return {"status": "ok", "mode": mode, "detail": detail}


def integration_fail(*, mode: str, detail: str) -> IntegrationCheck:
    return {"status": "fail", "mode": mode, "detail": detail}


@router.get("/ready")
async def ready() -> JSONResponse:
    checks: dict[str, Any] = {
        "database": await check_database(),
        "redis": await check_redis(),
        "integrations": await check_integrations(),
    }
    status = "ok" if all_checks_pass(checks) else "degraded"
    status_code = 200 if status == "ok" else 503
    return JSONResponse(status_code=status_code, content={"status": status, "checks": checks})


def all_checks_pass(checks: dict[str, Any]) -> bool:
    for value in checks.values():
        if isinstance(value, dict) and value.get("status") == "fail":
            return False
        if isinstance(value, dict) and not all_checks_pass(value):
            return False
        if value == "fail":
            return False
    return True


@router.get("/startup")
async def startup() -> JSONResponse:
    migrations = check_migrations()
    status_code = 200 if migrations.status == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if migrations.status == "ok" else "degraded",
            "checks": {
                "migrations": {
                    "status": migrations.status,
                    "current": migrations.current,
                    "head": migrations.head,
                    "detail": migrations.detail,
                }
            },
        },
    )


def check_migrations() -> MigrationState:
    return migration_state()
