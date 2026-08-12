from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app


client = TestClient(app)


def test_validation_error_is_standardized():
    app.dependency_overrides[get_current_user] = lambda: type(
        "User",
        (),
        {"role": "admin", "id": "test-user"},
    )()
    try:
        response = client.post("/rag/query", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"] == "Request validation failed."
    assert isinstance(body["errors"], list)


def test_openapi_metadata_and_rag_operation_are_documented():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    body = response.json()
    assert body["info"]["title"] == "BUYMA AI Platform API"
    assert body["info"]["version"] == "1.0.0"

    rag_operation = body["paths"]["/rag/query"]["post"]
    assert rag_operation["summary"] == "Run RAG query"
    assert "response_model" not in rag_operation
    assert "description" in rag_operation
    assert "422" in rag_operation["responses"]
