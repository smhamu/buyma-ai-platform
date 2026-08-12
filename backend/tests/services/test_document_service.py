from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import AppException
from app.services.document_service import DocumentService


class FakeRepository:
    def __init__(self, document):
        self.document = document
        self.deleted = []

    async def find_by_id(self, obj_id):
        return self.document

    async def delete(self, obj):
        self.deleted.append(obj)


@pytest.mark.asyncio
@pytest.mark.parametrize("ingestion_status", ["ready", "failed"])
async def test_delete_allows_terminal_ingestion_statuses(ingestion_status):
    document = SimpleNamespace(id=uuid4(), ingestion_status=ingestion_status)
    repository = FakeRepository(document)
    service = DocumentService(repository)

    result = await service.delete(document.id)

    assert result == {"id": str(document.id)}
    assert repository.deleted == [document]


@pytest.mark.asyncio
@pytest.mark.parametrize("ingestion_status", ["pending", "processing"])
async def test_delete_rejects_in_progress_ingestion_statuses(ingestion_status):
    document = SimpleNamespace(id=uuid4(), ingestion_status=ingestion_status)
    repository = FakeRepository(document)
    service = DocumentService(repository)

    with pytest.raises(AppException) as exc_info:
        await service.delete(document.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DOCUMENT_INGESTION_IN_PROGRESS"
    assert repository.deleted == []
