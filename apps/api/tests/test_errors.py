"""Tests for RFC 9457 Problem Details error code normalization."""

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import create_app


def test_http_exception_handler_uses_status_specific_problem_code() -> None:
    app = create_app()

    @app.get("/missing")
    async def missing() -> None:
        raise HTTPException(status_code=404, detail="Missing resource.")

    response = TestClient(app).get("/missing")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "not_found"
    assert response.json()["type"] == "https://prompteer.dev/errors/not-found"


def test_http_exception_handler_keeps_generic_code_for_unmapped_status() -> None:
    app = create_app()

    @app.get("/conflict")
    async def conflict() -> None:
        raise HTTPException(status_code=409, detail="Conflict.")

    response = TestClient(app).get("/conflict")

    assert response.status_code == 409
    assert response.json()["code"] == "http_error"


def test_http_exception_handler_preserves_security_headers() -> None:
    app = create_app()

    @app.get("/protected")
    async def protected() -> None:
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    response = TestClient(app).get("/protected")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "unauthorized"
