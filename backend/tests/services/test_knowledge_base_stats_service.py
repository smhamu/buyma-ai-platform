from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import NotFoundException
from app.services.knowledge_base_stats_service import KnowledgeBaseStatsService


class FakeKnowledgeBaseRepository:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base

    async def find_by_id(self, knowledge_base_id):
        return self.knowledge_base


class FakeStatsRepository:
    def __init__(
        self,
        document_stats=None,
        chunk_count=0,
        embedding_count=0,
    ):
        self.document_stats = document_stats or {
            "document_count": 0,
            "latest_document_count": 0,
            "ready_count": 0,
            "pending_count": 0,
            "processing_count": 0,
            "failed_count": 0,
        }
        self.chunk_count = chunk_count
        self.embedding_count = embedding_count

    async def get_document_stats(self, knowledge_base_id):
        return self.document_stats

    async def count_chunks(self, knowledge_base_id):
        return self.chunk_count

    async def count_embeddings(self, knowledge_base_id):
        return self.embedding_count


@pytest.mark.asyncio
async def test_get_stats_returns_empty_counts():
    service = KnowledgeBaseStatsService(
        knowledge_base_repository=FakeKnowledgeBaseRepository(SimpleNamespace()),
        stats_repository=FakeStatsRepository(),
    )

    result = await service.get_stats(uuid4())

    assert result.document_count == 0
    assert result.latest_document_count == 0
    assert result.ready_count == 0
    assert result.pending_count == 0
    assert result.processing_count == 0
    assert result.failed_count == 0
    assert result.chunk_count == 0
    assert result.embedding_count == 0


@pytest.mark.asyncio
async def test_get_stats_returns_document_chunk_and_embedding_counts():
    service = KnowledgeBaseStatsService(
        knowledge_base_repository=FakeKnowledgeBaseRepository(SimpleNamespace()),
        stats_repository=FakeStatsRepository(
            document_stats={
                "document_count": 5,
                "latest_document_count": 4,
                "ready_count": 3,
                "pending_count": 0,
                "processing_count": 0,
                "failed_count": 1,
            },
            chunk_count=12,
            embedding_count=11,
        ),
    )

    result = await service.get_stats(uuid4())

    assert result.document_count == 5
    assert result.latest_document_count == 4
    assert result.ready_count == 3
    assert result.failed_count == 1
    assert result.chunk_count == 12
    assert result.embedding_count == 11


@pytest.mark.asyncio
async def test_get_stats_raises_when_knowledge_base_missing():
    service = KnowledgeBaseStatsService(
        knowledge_base_repository=FakeKnowledgeBaseRepository(None),
        stats_repository=FakeStatsRepository(),
    )

    with pytest.raises(NotFoundException):
        await service.get_stats(uuid4())
