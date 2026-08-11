import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.schemas.retriever import RetrieverRequest
from app.services.retriever_service import RetrieverService


class RetrieverServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_retrieve_builds_numbered_context_and_forwards_request(self):
        model_id = uuid4()
        first_document_id = uuid4()
        first_chunk_id = uuid4()
        second_document_id = uuid4()
        second_chunk_id = uuid4()
        vector_search_service = SimpleNamespace(
            search=AsyncMock(
                return_value=[
                    SimpleNamespace(
                        document_id=first_document_id,
                        chunk_id=first_chunk_id,
                        content="First chunk",
                        distance="0.1",
                    ),
                    SimpleNamespace(
                        document_id=second_document_id,
                        chunk_id=second_chunk_id,
                        content="Second chunk",
                        distance=0.2,
                    ),
                ]
            )
        )
        service = RetrieverService(vector_search_service=vector_search_service)
        payload = RetrieverRequest(
            query="BUYMA rules",
            embedding_model_id=model_id,
            top_k=2,
        )

        result = await service.retrieve(payload)

        search_payload = vector_search_service.search.await_args.args[0]
        self.assertEqual(search_payload.query, payload.query)
        self.assertEqual(search_payload.embedding_model_id, model_id)
        self.assertEqual(search_payload.top_k, 2)
        self.assertEqual(search_payload.distance_threshold, 0.4)
        self.assertEqual(
            result.context,
            "[Context 1]\nFirst chunk\n\n[Context 2]\nSecond chunk",
        )
        self.assertEqual(len(result.chunks), 2)
        self.assertEqual(result.chunks[0].distance, 0.1)

    async def test_retrieve_returns_empty_context_when_no_chunks_are_found(self):
        vector_search_service = SimpleNamespace(search=AsyncMock(return_value=[]))
        service = RetrieverService(vector_search_service=vector_search_service)

        result = await service.retrieve(
            RetrieverRequest(
                query="No result",
                embedding_model_id=uuid4(),
            )
        )

        self.assertEqual(result.context, "")
        self.assertEqual(result.chunks, [])

    async def test_retrieve_removes_duplicate_chunk_ids(self):
        document_id = uuid4()
        chunk_id = uuid4()
        vector_search_service = SimpleNamespace(
            search=AsyncMock(
                return_value=[
                    SimpleNamespace(
                        document_id=document_id,
                        chunk_id=chunk_id,
                        content="Closest version",
                        distance=0.1,
                    ),
                    SimpleNamespace(
                        document_id=document_id,
                        chunk_id=chunk_id,
                        content="Duplicate version",
                        distance=0.2,
                    ),
                ]
            )
        )
        service = RetrieverService(vector_search_service=vector_search_service)

        result = await service.retrieve(
            RetrieverRequest(
                query="Duplicate chunks",
                embedding_model_id=uuid4(),
            )
        )

        self.assertEqual(len(result.chunks), 1)
        self.assertEqual(result.chunks[0].content, "Closest version")
        self.assertEqual(result.context, "[Context 1]\nClosest version")


if __name__ == "__main__":
    unittest.main()
