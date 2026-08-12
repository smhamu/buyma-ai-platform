from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.knowledge_bases import (
    create_knowledge_base,
    delete_knowledge_base,
    get_knowledge_base,
    get_knowledge_base_stats,
    list_knowledge_base_documents,
)
from app.schemas.knowledge_base import KnowledgeBaseCreate


def make_knowledge_base(**overrides):
    data = {
        "id": uuid4(),
        "name": "BUYMA出品ナレッジ",
        "description": "出品関連情報",
        "is_active": True,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.asyncio
async def test_create_knowledge_base_returns_response():
    knowledge_base = make_knowledge_base()
    service = SimpleNamespace(create=AsyncMock(return_value=knowledge_base))
    current_user = SimpleNamespace(id=uuid4())

    response = await create_knowledge_base(
        payload=KnowledgeBaseCreate(
            name=knowledge_base.name,
            description=knowledge_base.description,
        ),
        service=service,
        current_user=current_user,
    )

    service.create.assert_awaited_once_with(
        {
            "owner_user_id": current_user.id,
            "name": knowledge_base.name,
            "description": knowledge_base.description,
            "is_active": True,
        }
    )
    assert response["success"] is True
    assert response["data"].id == knowledge_base.id
    assert response["data"].name == knowledge_base.name


@pytest.mark.asyncio
async def test_get_knowledge_base_returns_response():
    knowledge_base = make_knowledge_base()
    authz = SimpleNamespace(
        require_knowledge_base_access=AsyncMock(return_value=knowledge_base)
    )
    current_user = SimpleNamespace()

    response = await get_knowledge_base(
        knowledge_base_id=knowledge_base.id,
        authz=authz,
        current_user=current_user,
    )

    authz.require_knowledge_base_access.assert_awaited_once_with(
        knowledge_base.id,
        current_user,
    )
    assert response["data"].id == knowledge_base.id


@pytest.mark.asyncio
async def test_delete_knowledge_base_returns_deleted_id():
    knowledge_base_id = uuid4()
    service = SimpleNamespace(
        delete=AsyncMock(return_value={"id": str(knowledge_base_id)})
    )
    authz = SimpleNamespace(require_knowledge_base_access=AsyncMock())
    current_user = SimpleNamespace()

    response = await delete_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        service=service,
        authz=authz,
        current_user=current_user,
    )

    authz.require_knowledge_base_access.assert_awaited_once_with(
        knowledge_base_id,
        current_user,
    )
    assert response["data"] == {"id": str(knowledge_base_id)}


@pytest.mark.asyncio
async def test_get_knowledge_base_stats_returns_counts():
    knowledge_base_id = uuid4()
    stats = SimpleNamespace(
        document_count=5,
        latest_document_count=4,
        ready_count=3,
        pending_count=0,
        processing_count=0,
        failed_count=1,
        chunk_count=12,
        embedding_count=11,
        model_dump=lambda: {
            "document_count": 5,
            "latest_document_count": 4,
            "ready_count": 3,
            "pending_count": 0,
            "processing_count": 0,
            "failed_count": 1,
            "chunk_count": 12,
            "embedding_count": 11,
        },
    )
    service = SimpleNamespace(get_stats=AsyncMock(return_value=stats))
    authz = SimpleNamespace(require_knowledge_base_access=AsyncMock())
    current_user = SimpleNamespace()

    response = await get_knowledge_base_stats(
        knowledge_base_id=knowledge_base_id,
        service=service,
        authz=authz,
        current_user=current_user,
    )

    authz.require_knowledge_base_access.assert_awaited_once_with(
        knowledge_base_id,
        current_user,
    )
    service.get_stats.assert_awaited_once_with(knowledge_base_id)
    assert response["success"] is True
    assert response["message"] == "Knowledge base stats fetched successfully."
    assert response["data"]["document_count"] == 5
    assert response["data"]["latest_document_count"] == 4
    assert response["data"]["ready_count"] == 3
    assert response["data"]["failed_count"] == 1
    assert response["data"]["chunk_count"] == 12
    assert response["data"]["embedding_count"] == 11


@pytest.mark.asyncio
async def test_list_knowledge_base_documents_returns_documents():
    knowledge_base_id = uuid4()
    document = SimpleNamespace(
        id=uuid4(),
        knowledge_base_id=knowledge_base_id,
        title="KB Document",
        content="content",
        source_type="manual",
        source_url=None,
        original_filename=None,
        mime_type=None,
        file_size=None,
        checksum=None,
        version=1,
        previous_document_id=None,
        version_group_id=uuid4(),
        is_latest=True,
        status="active",
        ingestion_status="ready",
    )

    service = SimpleNamespace(
        list_documents=AsyncMock(
            return_value={
                "items": [document],
                "total": 1,
                "total_pages": 1,
            }
        )
    )
    authz = SimpleNamespace(require_knowledge_base_access=AsyncMock())
    current_user = SimpleNamespace()

    response = await list_knowledge_base_documents(
        knowledge_base_id=knowledge_base_id,
        page=1,
        page_size=20,
        q=None,
        status=None,
        ingestion_status=None,
        is_latest=True,
        source_type=None,
        sort_by="created_at",
        sort_order="desc",
        service=service,
        authz=authz,
        current_user=current_user,
    )

    authz.require_knowledge_base_access.assert_awaited_once_with(
        knowledge_base_id,
        current_user,
    )
    service.list_documents.assert_awaited_once_with(
        knowledge_base_id=knowledge_base_id,
        page=1,
        page_size=20,
        q=None,
        status=None,
        ingestion_status=None,
        is_latest=True,
        source_type=None,
        sort_by="created_at",
        sort_order="desc",
    )
    assert response["data"]["items"][0]["knowledge_base_id"] == knowledge_base_id
    assert response["data"]["page"] == 1
    assert response["data"]["page_size"] == 20
    assert response["data"]["total"] == 1
    assert response["data"]["total_pages"] == 1
    assert response["data"]["sort_by"] == "created_at"
    assert response["data"]["sort_order"] == "desc"
