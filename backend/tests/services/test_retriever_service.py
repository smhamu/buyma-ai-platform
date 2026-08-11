from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.schemas.retriever import RetrieverRequest
from app.services.retriever_service import RetrieverService


@pytest.mark.asyncio
async def test_retrieve_builds_context_and_removes_duplicate_chunks():
    document_id = uuid4()
    chunk_id = uuid4()
    unique_chunk_id = uuid4()
    vector_search_service = SimpleNamespace(
        search=AsyncMock(
            return_value=[
                SimpleNamespace(
                    document_id=document_id,
                    chunk_id=chunk_id,
                    content="First chunk",
                    distance=0.1,
                ),
                SimpleNamespace(
                    document_id=document_id,
                    chunk_id=chunk_id,
                    content="Duplicate chunk",
                    distance=0.2,
                ),
                SimpleNamespace(
                    document_id=document_id,
                    chunk_id=unique_chunk_id,
                    content="Second chunk",
                    distance=0.3,
                ),
            ]
        )
    )
    service = RetrieverService(vector_search_service=vector_search_service)

    result = await service.retrieve(
        RetrieverRequest(
            query="Question",
            embedding_model_id=uuid4(),
            top_k=3,
        )
    )

    assert [chunk.chunk_id for chunk in result.chunks] == [chunk_id, unique_chunk_id]
    assert result.context == "[Context 1]\nFirst chunk\n\n[Context 2]\nSecond chunk"


@pytest.mark.asyncio
async def test_retrieve_returns_empty_context_for_no_results():
    service = RetrieverService(
        vector_search_service=SimpleNamespace(search=AsyncMock(return_value=[]))
    )

    result = await service.retrieve(
        RetrieverRequest(query="Question", embedding_model_id=uuid4())
    )

    assert result.context == ""
    assert result.chunks == []
