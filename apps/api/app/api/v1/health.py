from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, object]:
    return {
        "status": "ok",
        "checks": {
            "database": "not_checked_yet",
            "redis": "not_checked_yet",
            "integrations": "configured",
        },
    }


@router.get("/startup")
async def startup() -> dict[str, str]:
    return {"status": "ok", "migrations": "not_checked_yet"}
