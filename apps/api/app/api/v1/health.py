"""API v1 health probe routes; no sibling health API version exists yet."""

from collections.abc import Awaitable
from typing import Any, Literal, TypedDict, cast

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

router = APIRouter(prefix="/health", tags=["health"])

HealthStatus = Literal["ok", "fail", "disabled"]


class IntegrationCheck(TypedDict):
    status: HealthStatus
    mode: str
    detail: str


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


async def check_database() -> str:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return "fail"
    return "ok"


async def check_redis() -> str:
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    try:
        await cast(Awaitable[bool], client.ping())
    except Exception:
        return "fail"
    finally:
        await client.aclose()
    return "ok"


async def check_integrations() -> dict[str, IntegrationCheck]:
    modes = integration_modes()
    flags = feature_flags()
    return {
        "google_oauth": check_google_oauth(mode=modes["google_oauth"]),
        "llm": check_featured_integration(
            feature_enabled=flags["llm"],
            mode=modes["llm"],
            mock_detail="deterministic LLM mock client is selected",
            real_detail="real LLM provider credentials are configured",
        ),
        "stripe": check_featured_integration(
            feature_enabled=flags["payments"],
            mode=modes["stripe"],
            mock_detail="local Stripe mock checkout is selected",
            real_detail="real Stripe credentials are configured",
        ),
        "email": check_featured_integration(
            feature_enabled=flags["email"],
            mode=modes["email"],
            mock_detail="local SendGrid mock mailbox is selected",
            real_detail="real SendGrid credentials are configured",
        ),
    }


def check_google_oauth(*, mode: str) -> IntegrationCheck:
    if bool(settings.google_client_id) != bool(settings.google_client_secret):
        return {
            "status": "fail",
            "mode": "partial",
            "detail": "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set together.",
        }
    if mode == "real":
        return {
            "status": "ok",
            "mode": mode,
            "detail": "real Google OAuth credentials are configured",
        }
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


def check_featured_integration(
    *,
    feature_enabled: bool,
    mode: str,
    mock_detail: str,
    real_detail: str,
) -> IntegrationCheck:
    if not feature_enabled:
        return {"status": "disabled", "mode": mode, "detail": "feature flag is disabled"}
    if mode == "real":
        return {"status": "ok", "mode": mode, "detail": real_detail}
    if dev_routes_enabled():
        return {"status": "ok", "mode": mode, "detail": mock_detail}
    return {
        "status": "fail",
        "mode": mode,
        "detail": "mock mode requires dev routes or real provider credentials.",
    }


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
        if value == "fail":
            return False
        if isinstance(value, dict) and not all_checks_pass(value):
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
