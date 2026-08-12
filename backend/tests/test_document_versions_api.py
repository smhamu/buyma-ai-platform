from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1.document_versions import (
    list_document_versions,
    restore_document_version,
)
from app.common.exceptions import NotFoundException


def make_document(**overrides):
    data = {
        "id": uuid4(),
        "knowledge_base_id": None,
        "title": "rule",
        "content": "content",
        "source_type": "file",
        "source_url": None,
        "original_filename": "rule.txt",
        "mime_type": "text/plain",
        "file_size": 10,
        "checksum": "a" * 64,
        "version": 1,
        "previous_document_id": None,
        "version_group_id": uuid4(),
        "is_latest": True,
        "status": "active",
        "ingestion_status": "ready",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class FakeRepository:
    def __init__(self, document, versions=None):
        self.document = document
        self.versions = versions or []

    async def find_by_id(self, document_id):
        return self.document

    async def find_versions_by_group(self, version_group_id):
        return self.versions


class FakeRollbackService:
    def __init__(self, result):
        self.result = result
        self.restored_ids = []

    async def restore(self, document_id):
        self.restored_ids.append(document_id)
        return self.result


@pytest.mark.asyncio
async def test_list_document_versions_returns_all_versions():
    version_group_id = uuid4()
    v1 = make_document(version=1, version_group_id=version_group_id, is_latest=False)
    v2 = make_document(
        version=2,
        version_group_id=version_group_id,
        previous_document_id=v1.id,
        is_latest=True,
    )

    from app.api.v1 import document_versions as module

    original_repository = module.DocumentRepository
    module.DocumentRepository = lambda _: FakeRepository(v2, [v1, v2])
    try:
        response = await list_document_versions(
            document_id=v2.id,
            db=SimpleNamespace(),
            current_user=SimpleNamespace(),
        )
    finally:
        module.DocumentRepository = original_repository

    assert [item.version for item in response["data"]] == [1, 2]
    assert response["data"][0].is_latest is False
    assert response["data"][1].is_latest is True


@pytest.mark.asyncio
async def test_list_document_versions_raises_when_document_missing():
    from app.api.v1 import document_versions as module

    original_repository = module.DocumentRepository
    module.DocumentRepository = lambda _: FakeRepository(None)
    try:
        with pytest.raises(NotFoundException):
            await list_document_versions(
                document_id=uuid4(),
                db=SimpleNamespace(),
                current_user=SimpleNamespace(),
            )
    finally:
        module.DocumentRepository = original_repository


@pytest.mark.asyncio
async def test_restore_document_version_returns_new_document():
    restored_from = make_document(version=1, is_latest=False)
    new_document = make_document(
        version=3,
        previous_document_id=uuid4(),
        is_latest=True,
    )
    service = FakeRollbackService(
        {
            "restored_from_document_id": restored_from.id,
            "restored_from_version": restored_from.version,
            "new_document": new_document,
            "task_ids": ["task-id"],
        }
    )

    response = await restore_document_version(
        document_id=restored_from.id,
        service=service,
        current_user=SimpleNamespace(),
    )

    assert service.restored_ids == [restored_from.id]
    assert response["success"] is True
    assert response["message"] == "Document version restored successfully."
    assert response["data"]["restored_from_document_id"] == restored_from.id
    assert response["data"]["restored_from_version"] == 1
    assert response["data"]["new_document"]["version"] == 3
    assert response["data"]["new_document"]["is_latest"] is True
    assert response["data"]["task_ids"] == ["task-id"]
