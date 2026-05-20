from collections.abc import Awaitable
from typing import cast

from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.migrations import MigrationState, migration_state
from app.db.session import engine

router = APIRouter(prefix="/health", tags=["health"])


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


@router.get("/ready")
async def ready() -> JSONResponse:
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "integrations": "configured",
    }
    status = "ok" if all(value != "fail" for value in checks.values()) else "degraded"
    status_code = 200 if status == "ok" else 503
    return JSONResponse(status_code=status_code, content={"status": status, "checks": checks})


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
