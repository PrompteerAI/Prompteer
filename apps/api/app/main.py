import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.bootstrap import bootstrap_development_state, integration_modes
from app.core.config import settings
from app.core.errors import (
    ProblemException,
    http_exception_handler,
    problem_exception_handler,
    problem_response,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.observability import init_observability
from app.core.ratelimit import limiter
from app.integrations.email.mock import router as mock_sendgrid_router
from app.integrations.google_oauth.mock import router as mock_google_oauth_router
from app.integrations.llm.mock import router as mock_llm_router
from app.integrations.payments.mock import router as mock_stripe_router

logger = structlog.get_logger(__name__)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def is_valid_request_id(value: str) -> bool:
    return bool(REQUEST_ID_PATTERN.fullmatch(value))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await bootstrap_development_state()
    logger.info("integrations_selected", **integration_modes())
    yield


async def starlette_http_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, StarletteHTTPException):
        return await http_exception_handler(request, exc)
    raise exc


async def request_validation_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, RequestValidationError):
        return await validation_exception_handler(request, exc)
    raise exc


async def app_problem_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, ProblemException):
        return await problem_exception_handler(request, exc)
    raise exc


async def app_unhandled_exception_handler(request: Request, exc: Exception) -> Response:
    return await unhandled_exception_handler(request, exc)


def create_app() -> FastAPI:
    configure_logging()
    init_observability()

    app = FastAPI(title="Prompteer API", version="0.1.0", lifespan=lifespan)
    app.state.limiter = limiter

    app.add_middleware(CorrelationIdMiddleware, validator=is_valid_request_id)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(settings.app_url).rstrip("/")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(ProblemException, app_problem_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(Exception, app_unhandled_exception_handler)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
        response = problem_response(
            request=request,
            status_code=429,
            title="Too Many Requests",
            detail=f"Rate limit exceeded: {exc.detail}",
            code="rate_limited",
        )
        return limiter._inject_headers(response, request.state.view_rate_limit)  # noqa: SLF001

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "Welcome to Prompteer"}

    @app.get("/api/v1/integrations")
    async def integrations() -> dict[str, str]:
        return integration_modes()

    app.include_router(api_router)
    app.include_router(mock_google_oauth_router)
    app.include_router(mock_llm_router)
    app.include_router(mock_stripe_router)
    app.include_router(mock_sendgrid_router)
    return app


app = create_app()
