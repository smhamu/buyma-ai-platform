from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1 import products as products_module
from app.common.exceptions import AppException
from app.core.security_utils import sanitize_error_message
from app.main import app
from app.schemas.prompt_builder import PromptBuildRequest
from app.schemas.rag import RAGQueryRequest
from app.schemas.retriever import RetrieverRequest
from app.schemas.vector_search import VectorSearchRequest
from app.services.document_file_ingestion_service import DocumentFileIngestionService


class FakeProductService:
    async def list(self):
        return []

    async def get(self, product_id):
        return SimpleNamespace(id=product_id, name="p", brand=None, category=None, description=None, price=None)

    async def update(self, product_id, payload):
        return SimpleNamespace(id=product_id, name="p", brand=None, category=None, description=None, price=None)

    async def delete(self, product_id):
        return {"id": str(product_id)}


class FakeDb:
    def in_transaction(self):
        return False

    def begin(self):
        return FakeTransaction()

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def flush(self):
        return None


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


def make_file_service():
    return DocumentFileIngestionService(
        db=FakeDb(),
        ingestion_service=SimpleNamespace(ingest_in_transaction=None),
        document_repository=SimpleNamespace(),
    )


def test_products_requires_authentication(monkeypatch):
    app.dependency_overrides[products_module.get_product_service] = lambda: FakeProductService()
    try:
        client = TestClient(app)
        response = client.get("/products")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


@pytest.mark.parametrize(
    "schema_class",
    [
        VectorSearchRequest,
        RetrieverRequest,
        PromptBuildRequest,
        RAGQueryRequest,
    ],
)
def test_query_schemas_reject_blank_query(schema_class):
    with pytest.raises(ValidationError):
        schema_class(
            query="   ",
            embedding_model_id=uuid4(),
        )


@pytest.mark.parametrize(
    "schema_class",
    [
        VectorSearchRequest,
        RetrieverRequest,
        PromptBuildRequest,
        RAGQueryRequest,
    ],
)
def test_query_schemas_reject_too_large_query(schema_class):
    with pytest.raises(ValidationError):
        schema_class(
            query="a" * 4001,
            embedding_model_id=uuid4(),
        )


def test_file_ingestion_rejects_pdf_extension_with_invalid_signature():
    service = make_file_service()

    with pytest.raises(AppException) as exc_info:
        service._validate_file_signature_and_type(
            extension=".pdf",
            file_content=b"MZ fake exe",
            mime_type="application/pdf",
        )

    assert exc_info.value.status_code == 415
    assert exc_info.value.code == "UNSUPPORTED_DOCUMENT_FILE"


def test_file_ingestion_rejects_binary_text_upload():
    service = make_file_service()

    with pytest.raises(AppException) as exc_info:
        service._validate_file_signature_and_type(
            extension=".txt",
            file_content=b"abc\x00def",
            mime_type="text/plain",
        )

    assert exc_info.value.status_code == 415
    assert exc_info.value.code == "UNSUPPORTED_DOCUMENT_FILE"


def test_sanitize_error_message_redacts_sensitive_tokens():
    message = (
        "Bearer secret.token "
        "sk-proj-secret-key "
        "postgresql+asyncpg://user:pass@host/db "
        "redis://redis:6379/0"
    )

    sanitized = sanitize_error_message(message)

    assert "secret.token" not in sanitized
    assert "sk-proj-secret-key" not in sanitized
    assert "postgresql+asyncpg://" not in sanitized
    assert "redis://redis:6379/0" not in sanitized
    assert sanitized.count("[REDACTED]") >= 4


def test_cors_allowed_origins_are_configured():
    cors_middleware = next(
        middleware for middleware in app.user_middleware
        if middleware.cls.__name__ == "CORSMiddleware"
    )

    assert "http://localhost:3000" in cors_middleware.kwargs["allow_origins"]
    assert cors_middleware.kwargs["allow_credentials"] is False
