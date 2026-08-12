from app.schemas.retriever import (
    RetrievedChunk,
    RetrieverRequest,
    RetrieverResponse,
)
from app.schemas.vector_search import VectorSearchRequest
from app.services.vector_search_service import VectorSearchService


class RetrieverService:
    def __init__(self, vector_search_service: VectorSearchService):
        self.vector_search_service = vector_search_service

    async def retrieve(self, payload: RetrieverRequest) -> RetrieverResponse:
        results = await self.vector_search_service.search(
            VectorSearchRequest(
                query=payload.query,
                embedding_model_id=payload.embedding_model_id,
                knowledge_base_id=payload.knowledge_base_id,
                top_k=payload.top_k,
                distance_threshold=payload.distance_threshold,
            )
        )

        chunks = self._deduplicate_chunks(results)

        return RetrieverResponse(
            query=payload.query,
            context=self._build_context(chunks),
            chunks=chunks,
        )

    @staticmethod
    def _build_context(chunks: list[RetrievedChunk]) -> str:
        return "\n\n".join(
            f"[Context {index}]\n{chunk.content}"
            for index, chunk in enumerate(chunks, start=1)
        )

    @staticmethod
    def _deduplicate_chunks(results) -> list[RetrievedChunk]:
        chunks = []
        seen_chunk_ids = set()

        for row in results:
            if row.chunk_id in seen_chunk_ids:
                continue

            seen_chunk_ids.add(row.chunk_id)
            chunks.append(
                RetrievedChunk(
                    document_id=row.document_id,
                    chunk_id=row.chunk_id,
                    content=row.content,
                    distance=float(row.distance),
                )
            )

        return chunks
