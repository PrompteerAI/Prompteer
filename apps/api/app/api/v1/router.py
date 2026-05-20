from fastapi import APIRouter

from app.api.v1.billing import router as billing_router
from app.api.v1.challenges import router as challenges_router
from app.api.v1.community import router as community_router
from app.api.v1.dev import router as dev_router
from app.api.v1.health import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(dev_router)
api_router.include_router(challenges_router)
api_router.include_router(billing_router)
api_router.include_router(community_router)
