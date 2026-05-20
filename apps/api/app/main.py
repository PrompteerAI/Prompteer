from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import http_exception_handler, validation_exception_handler
from app.core.logging import configure_logging
from app.core.observability import init_observability
from app.core.ratelimit import limiter
from app.integrations.google_oauth.mock import router as mock_google_oauth_router


async def starlette_http_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)
    raise exc


async def request_validation_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, RequestValidationError):
        return await validation_exception_handler(request, exc)
    raise exc


def create_app() -> FastAPI:
    configure_logging()
    init_observability()

    app = FastAPI(title="Prompteer API", version="0.1.0")
    app.state.limiter = limiter

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(settings.app_url).rstrip("/")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):  # type: ignore[no-untyped-def]
        return await http_exception_handler(request, exc)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "Welcome to Prompteer"}

    @app.get("/api/v1/integrations")
    async def integrations() -> dict[str, str]:
        return {
            "llm": "real" if settings.openai_api_key or settings.anthropic_api_key else "mock",
            "google_oauth": "real"
            if settings.google_client_id and settings.google_client_secret
            else "mock",
            "stripe": "real" if settings.stripe_secret_key else "mock",
            "email": "real" if settings.sendgrid_api_key else "mock",
        }

    app.include_router(api_router)
    app.include_router(mock_google_oauth_router)
    return app


app = create_app()
