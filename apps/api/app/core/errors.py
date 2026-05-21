# RFC 9457 Problem Details handlers shared by API v1 and platform middleware.
# Unexpected exceptions are captured for observability before returning JSON.

from http import HTTPStatus
from typing import Any

import structlog
from asgi_correlation_id import correlation_id
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.observability import capture_exception

logger = structlog.get_logger(__name__)

HTTP_ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
}


class ProblemException(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        title: str,
        detail: str,
        code: str,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.code = code
        self.errors = errors


def request_id_for(request: Request) -> str | None:
    return correlation_id.get() or request.headers.get("X-Request-ID")


def problem_response(
    *,
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    errors: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"https://prompteer.dev/errors/{code.replace('_', '-')}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
        "code": code,
        "request_id": request_id_for(request),
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=body,
        headers=headers,
        media_type="application/problem+json",
    )


async def problem_exception_handler(request: Request, exc: ProblemException) -> JSONResponse:
    return problem_response(
        request=request,
        status_code=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        code=exc.code,
        errors=exc.errors,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    title = HTTPStatus(exc.status_code).phrase
    return problem_response(
        request=request,
        status_code=exc.status_code,
        title=title,
        detail=str(exc.detail),
        code=http_error_code(exc.status_code),
    )


def http_error_code(status_code: int) -> str:
    return HTTP_ERROR_CODES.get(status_code, "http_error")


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return problem_response(
        request=request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation Error",
        detail="The request payload or parameters are invalid.",
        code="validation_error",
        errors=[
            {
                "loc": list(error["loc"]),
                "msg": str(error["msg"]),
                "type": str(error["type"]),
            }
            for error in exc.errors()
        ],
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    capture_exception(exc)
    logger.error(
        "unhandled_exception",
        path=str(request.url.path),
        request_id=request_id_for(request),
        exc_info=exc,
    )
    return problem_response(
        request=request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected server error occurred.",
        code="internal_server_error",
    )
