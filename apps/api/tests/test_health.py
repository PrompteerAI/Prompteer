from fastapi.testclient import TestClient

from app.main import app


def test_liveness_probe() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_integrations_default_to_mocks() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/integrations")
    assert response.status_code == 200
    assert response.json() == {
        "llm": "mock",
        "google_oauth": "mock",
        "stripe": "mock",
        "email": "mock",
    }
