from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.common.exceptions import AppException, NotFoundException
from app.services.document_file_ingestion_service import (
    DocumentFileIngestionService,
)


class FakeDb:
    def __init__(self):
        self.commit_count = 0
        self.flush_count = 0
        self.rollback_count = 0

    def in_transaction(self):
        return False

    async def commit(self):
        self.commit_count += 1

    async def rollback(self):
        self.rollback_count += 1

    async def flush(self):
        self.flush_count += 1

    def begin(self):
        return FakeTransaction()


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeIngestionService:
    def __init__(self):
        self.ingest_in_transaction = AsyncMock(
            return_value={
                "document": SimpleNamespace(id=uuid4()),
                "chunks": [],
                "embedding_jobs": [],
            }
        )


class FakeDocumentRepository:
    def __init__(self, latest_document=None):
        self.latest_document = latest_document
        self.find_latest_by_filename_calls = []
        self.db = FakeDb()

    async def find_latest_by_filename(
        self,
        *,
        knowledge_base_id,
        original_filename,
    ):
        self.find_latest_by_filename_calls.append(
            {
                "knowledge_base_id": knowledge_base_id,
                "original_filename": original_filename,
            }
        )
        return self.latest_document


def make_service(ingestion_service=None, latest_document=None):
    repository = FakeDocumentRepository(latest_document)
    service = DocumentFileIngestionService(
        db=repository.db,
        ingestion_service=ingestion_service or FakeIngestionService(),
        document_repository=repository,
    )
    return service, repository


@pytest.mark.asyncio
async def test_first_upload_sets_version_1_and_metadata():
    ingestion_service = FakeIngestionService()
    service, repository = make_service(ingestion_service=ingestion_service)
    embedding_model_id = uuid4()
    knowledge_base_id = uuid4()
    content_bytes = "BUYMA price rule".encode("utf-8")

    result = await service.ingest_file(
        filename="rule.txt",
        file_content=content_bytes,
        embedding_model_id=embedding_model_id,
        mime_type="text/plain",
        knowledge_base_id=knowledge_base_id,
        chunk_size=500,
    )

    payload = ingestion_service.ingest_in_transaction.await_args.args[0]
    assert payload.title == "rule"
    assert payload.content == "BUYMA price rule"
    assert payload.source_type == "file"
    assert payload.original_filename == "rule.txt"
    assert payload.mime_type == "text/plain"
    assert payload.file_size == len(content_bytes)
    assert len(payload.checksum) == 64
    assert payload.version == 1
    assert payload.previous_document_id is None
    assert payload.version_group_id is not None
    assert payload.is_latest is True
    assert payload.embedding_model_id == embedding_model_id
    assert payload.knowledge_base_id == knowledge_base_id
    assert repository.find_latest_by_filename_calls == [
        {
            "knowledge_base_id": knowledge_base_id,
            "original_filename": "rule.txt",
        }
    ]
    assert result["filename"] == "rule.txt"
    assert result["file_size"] == len(content_bytes)


@pytest.mark.asyncio
async def test_same_filename_changed_content_creates_next_version():
    previous_id = uuid4()
    version_group_id = uuid4()
    latest_document = SimpleNamespace(
        id=previous_id,
        checksum="old-checksum",
        version=1,
        version_group_id=version_group_id,
        is_latest=True,
    )
    ingestion_service = FakeIngestionService()
    service, repository = make_service(
        ingestion_service=ingestion_service,
        latest_document=latest_document,
    )

    await service.ingest_file(
        filename="rule.txt",
        file_content=b"new content",
        embedding_model_id=uuid4(),
    )

    payload = ingestion_service.ingest_in_transaction.await_args.args[0]
    assert latest_document.is_latest is False
    assert repository.db.commit_count == 0
    assert repository.db.flush_count == 1
    assert payload.version == 2
    assert payload.previous_document_id == previous_id
    assert payload.version_group_id == version_group_id
    assert payload.is_latest is True


@pytest.mark.asyncio
async def test_same_filename_same_checksum_rejects_duplicate():
    content = b"same content"
    from app.utils.checksum import calculate_sha256

    latest_document = SimpleNamespace(
        id=uuid4(),
        checksum=calculate_sha256(content),
        version=1,
        version_group_id=uuid4(),
        is_latest=True,
    )
    service, repository = make_service(latest_document=latest_document)

    with pytest.raises(AppException) as exc_info:
        await service.ingest_file(
            filename="rule.txt",
            file_content=content,
            embedding_model_id=uuid4(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DUPLICATE_DOCUMENT_FILE"
    assert latest_document.is_latest is True
    assert repository.db.commit_count == 0


@pytest.mark.asyncio
async def test_different_filename_uses_separate_version_group():
    ingestion_service = FakeIngestionService()
    service, repository = make_service(ingestion_service=ingestion_service)

    await service.ingest_file(
        filename="other.txt",
        file_content=b"content",
        embedding_model_id=uuid4(),
    )

    payload = ingestion_service.ingest_in_transaction.await_args.args[0]
    assert payload.version == 1
    assert repository.find_latest_by_filename_calls[0]["original_filename"] == "other.txt"


@pytest.mark.asyncio
async def test_ingest_markdown_extracts_content():
    ingestion_service = FakeIngestionService()
    service, _ = make_service(ingestion_service)

    await service.ingest_file(
        filename="buyma_shipping.md",
        file_content="# BUYMA発送対応".encode("utf-8"),
        embedding_model_id=uuid4(),
    )

    payload = ingestion_service.ingest_in_transaction.await_args.args[0]
    assert payload.title == "buyma_shipping"
    assert payload.content == "# BUYMA発送対応"


@pytest.mark.asyncio
async def test_ingest_rejects_unsupported_extension():
    service, _ = make_service()

    with pytest.raises(AppException) as exc_info:
        await service.ingest_file(
            filename="test.xlsx",
            file_content=b"content",
            embedding_model_id=uuid4(),
        )

    assert exc_info.value.status_code == 415
    assert exc_info.value.code == "UNSUPPORTED_DOCUMENT_FILE"


@pytest.mark.asyncio
async def test_ingest_rejects_empty_file():
    service, _ = make_service()

    with pytest.raises(AppException) as exc_info:
        await service.ingest_file(
            filename="empty.txt",
            file_content=b"",
            embedding_model_id=uuid4(),
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "DOCUMENT_TEXT_EXTRACTION_FAILED"


@pytest.mark.asyncio
async def test_ingest_rejects_large_file():
    service, _ = make_service()

    with pytest.raises(AppException) as exc_info:
        await service.ingest_file(
            filename="large.txt",
            file_content=b"a" * (10 * 1024 * 1024 + 1),
            embedding_model_id=uuid4(),
        )

    assert exc_info.value.status_code == 413
    assert exc_info.value.code == "DOCUMENT_FILE_TOO_LARGE"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception",
    [
        NotFoundException("KnowledgeBase"),
        AppException(
            status_code=409,
            code="KNOWLEDGE_BASE_INACTIVE",
            message="Knowledge base is inactive.",
        ),
    ],
)
async def test_ingest_propagates_knowledge_base_errors(exception):
    ingestion_service = FakeIngestionService()
    ingestion_service.ingest_in_transaction.side_effect = exception
    service, _ = make_service(ingestion_service)

    with pytest.raises(type(exception)):
        await service.ingest_file(
            filename="buyma.txt",
            file_content=b"content",
            embedding_model_id=uuid4(),
            knowledge_base_id=uuid4(),
        )
