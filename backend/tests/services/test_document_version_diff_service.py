from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import AppException, NotFoundException
from app.services.document_version_diff_service import DocumentVersionDiffService


def make_document(**overrides):
    data = {
        "id": uuid4(),
        "content": "line 1\nline 2",
        "version": 1,
        "version_group_id": uuid4(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class FakeDocumentRepository:
    def __init__(self, documents):
        self.documents = documents

    async def find_by_id(self, document_id):
        return self.documents.get(document_id)


def make_service(*documents):
    return DocumentVersionDiffService(
        document_repository=FakeDocumentRepository(
            {document.id: document for document in documents}
        )
    )


@pytest.mark.asyncio
async def test_compare_returns_added_removed_and_unchanged_lines():
    version_group_id = uuid4()
    base = make_document(
        content="keep\nremove\nsame",
        version=1,
        version_group_id=version_group_id,
    )
    compare = make_document(
        content="keep\nadd\nsame",
        version=2,
        version_group_id=version_group_id,
    )
    service = make_service(base, compare)

    result = await service.compare(base.id, compare.id)

    assert result.base_document_id == base.id
    assert result.base_version == 1
    assert result.compare_document_id == compare.id
    assert result.compare_version == 2
    assert [(line.type, line.content) for line in result.lines] == [
        ("unchanged", "keep"),
        ("removed", "remove"),
        ("added", "add"),
        ("unchanged", "same"),
    ]
    assert result.added_count == 1
    assert result.removed_count == 1
    assert result.unchanged_count == 2
    assert result.has_changes is True


@pytest.mark.asyncio
async def test_compare_same_document_has_no_changes():
    document = make_document(content="line 1\nline 2", version=1)
    service = make_service(document)

    result = await service.compare(document.id, document.id)

    assert [(line.type, line.content) for line in result.lines] == [
        ("unchanged", "line 1"),
        ("unchanged", "line 2"),
    ]
    assert result.added_count == 0
    assert result.removed_count == 0
    assert result.unchanged_count == 2
    assert result.has_changes is False


@pytest.mark.asyncio
async def test_compare_raises_when_version_groups_differ():
    base = make_document(version_group_id=uuid4())
    compare = make_document(version_group_id=uuid4())
    service = make_service(base, compare)

    with pytest.raises(AppException) as exc_info:
        await service.compare(base.id, compare.id)

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "DOCUMENT_VERSION_GROUP_MISMATCH"


@pytest.mark.asyncio
async def test_compare_raises_when_base_document_missing():
    compare = make_document()
    service = make_service(compare)

    with pytest.raises(NotFoundException):
        await service.compare(uuid4(), compare.id)


@pytest.mark.asyncio
async def test_compare_raises_when_compare_document_missing():
    base = make_document()
    service = make_service(base)

    with pytest.raises(NotFoundException):
        await service.compare(base.id, uuid4())
