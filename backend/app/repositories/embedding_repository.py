from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.models.embedding import Embedding
from app.repositories.base_repository import BaseRepository


class EmbeddingRepository(BaseRepository[Embedding]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Embedding)

    async def find_by_chunk_id(self, chunk_id: UUID) -> list[Embedding]:
        result = await self.db.execute(
            select(Embedding)
            .where(Embedding.chunk_id == chunk_id)
            .order_by(Embedding.created_at.desc())
        )
        return list(result.scalars().all())

    async def vector_search(
        self,
        query_vector: list[float],
        embedding_model_id: UUID,
        top_k: int = 5,
    ):
        distance = Embedding.vector.cosine_distance(query_vector)

        result = await self.db.execute(
            select(
                Embedding.id.label("embedding_id"),
                Embedding.document_id,
                Embedding.chunk_id,
                DocumentChunk.content,
                distance.label("distance"),
            )
            .join(DocumentChunk, DocumentChunk.id == Embedding.chunk_id)
            .where(
                Embedding.embedding_model_id == embedding_model_id,
                Embedding.status == "active",
            )
            .order_by(distance)
            .limit(top_k)
        )

        return result.all()