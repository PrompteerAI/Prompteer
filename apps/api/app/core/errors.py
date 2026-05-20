from http import HTTPStatus
from typing import Any

from asgi_correlation_id import correlation_id
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException


def problem_response(
    *,
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    code: str,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"https://prompteer.dev/errors/{code.replace('_', '-')}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
        "code": code,
        "request_id": correlation_id.get(),
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type="application/problem+json",
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    title = HTTPStatus(exc.status_code).phrase
    return problem_response(
        request=request,
        status_code=exc.status_code,
        title=title,
        detail=str(exc.detail),
        code="http_error",
    )


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
