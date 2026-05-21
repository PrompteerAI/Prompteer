"""FastAPI application assembly, middleware, routers, and exception handlers."""

import re
from collections.abc import AsyncIterator, Awaitable, Callable
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
from app.core.feature_flags import dev_routes_enabled
from app.core.logging import configure_logging
from app.core.observability import init_observability
from app.core.ratelimit import limiter
from app.integrations.email.mock import router as mock_sendgrid_router
from app.integrations.google_oauth.mock import router as mock_google_oauth_router
from app.integrations.llm.mock import router as mock_llm_router
from app.integrations.payments.mock import router as mock_stripe_router

logger = structlog.get_logger(__name__)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
API_MOCK_STRIPE_COMPLETE_PATTERN = re.compile(
    r"^/api/v1/billing/checkout/[^/]+/complete$",
)

LLM_MOCK_PATHS = frozenset(("/v1/chat/completions", "/v1/messages"))
GOOGLE_OAUTH_MOCK_PATHS = frozenset(
    (
        "/.well-known/openid-configuration",
        "/o/oauth2/v2/auth",
        "/token",
        "/v3/userinfo",
        "/oauth2/v3/certs",
    )
)
SENDGRID_MOCK_PATHS = frozenset(("/v3/mail/send",))
STRIPE_MOCK_EXACT_PATHS = frozenset(("/v1/checkout/sessions", "/dev/stripe/complete"))
STRIPE_MOCK_PREFIXES = ("/v1/checkout/sessions/",)


def is_valid_request_id(value: str) -> bool:
    return bool(REQUEST_ID_PATTERN.fullmatch(value))


def hidden_mock_route_provider(path: str) -> str | None:
    if path in LLM_MOCK_PATHS:
        return "llm"
    if path in GOOGLE_OAUTH_MOCK_PATHS:
        return "google_oauth"
    if path in SENDGRID_MOCK_PATHS:
        return "email"
    if path in STRIPE_MOCK_EXACT_PATHS or path.startswith(STRIPE_MOCK_PREFIXES):
        return "stripe"
    if API_MOCK_STRIPE_COMPLETE_PATTERN.fullmatch(path):
        return "stripe"
    return None


def inactive_mock_route_provider(path: str) -> str | None:
    provider = hidden_mock_route_provider(path)
    if provider is None:
        return None
    modes = integration_modes()
    if not dev_routes_enabled():
        return provider
    if (
        (provider == "llm" and modes["llm"] != "mock")
        or (provider == "google_oauth" and modes["google_oauth"] != "mock")
        or (provider == "email" and modes["email"] != "mock")
        or (provider == "stripe" and modes["stripe"] != "mock")
    ):
        return provider
    return None


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

    @app.middleware("http")
    async def hide_inactive_mock_routes(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if inactive_mock_route_provider(str(request.url.path)) is not None:
            return problem_response(
                request=request,
                status_code=404,
                title="Not Found",
                detail="Not found",
                code="not_found",
            )
        return await call_next(request)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
        response = problem_response(
            request=request,
            status_code=429,
            title="Too Many Requests",
            detail=f"Rate limit exceeded: {exc.detail}",
            code="rate_limited",
        )
        return limiter._inject_headers(response, request.state.view_rate_limit)

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
