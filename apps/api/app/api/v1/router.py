from fastapi import APIRouter

from app.api.v1.dev import router as dev_router
from app.api.v1.health import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(dev_router)
