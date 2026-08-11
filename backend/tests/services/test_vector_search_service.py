from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.common.exceptions import NotFoundException
from app.schemas.vector_search import VectorSearchRequest
from app.services.vector_search_service import VectorSearchService


@pytest.mark.asyncio
async def test_search_returns_results_and_forwards_top_k():
    model_id = uuid4()
    expected_results = [SimpleNamespace(chunk_id=uuid4())]
    model_repository = SimpleNamespace(
        find_by_id_with_provider=AsyncMock(
            return_value=SimpleNamespace(
                model_name="embedding-model",
                dimension=1536,
                provider=SimpleNamespace(provider_code="openai"),
            )
        )
    )
    embedding_repository = SimpleNamespace(
        vector_search=AsyncMock(return_value=expected_results)
    )
    embedding_provider = SimpleNamespace(
        generate_embedding=AsyncMock(return_value=[0.1, 0.2])
    )
    service = VectorSearchService(
        embedding_repository=embedding_repository,
        model_repository=model_repository,
    )
    payload = VectorSearchRequest(
        query="BUYMA rules",
        embedding_model_id=model_id,
        top_k=7,
    )

    with patch(
        "app.services.vector_search_service.EmbeddingProviderFactory.create",
        return_value=embedding_provider,
    ) as create_provider:
        results = await service.search(payload)

    assert results == expected_results
    create_provider.assert_called_once_with(
        provider_code="openai",
        model_name="embedding-model",
    )
    embedding_provider.generate_embedding.assert_awaited_once_with(
        text=payload.query,
        dimension=1536,
    )
    embedding_repository.vector_search.assert_awaited_once_with(
        query_vector=[0.1, 0.2],
        embedding_model_id=model_id,
        top_k=7,
    )


@pytest.mark.asyncio
async def test_search_raises_404_when_embedding_model_does_not_exist():
    model_repository = SimpleNamespace(
        find_by_id_with_provider=AsyncMock(return_value=None)
    )
    embedding_repository = SimpleNamespace(vector_search=AsyncMock())
    service = VectorSearchService(
        embedding_repository=embedding_repository,
        model_repository=model_repository,
    )

    with pytest.raises(NotFoundException) as exc_info:
        await service.search(
            VectorSearchRequest(
                query="Question",
                embedding_model_id=uuid4(),
            )
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "EMBEDDINGMODEL_NOT_FOUND"
    embedding_repository.vector_search.assert_not_awaited()
