from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.repositories.base_repository import BaseRepository


class DocumentChunkRepository(BaseRepository[DocumentChunk]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, DocumentChunk)

    async def find_by_document_id(self, document_id: UUID) -> list[DocumentChunk]:
        result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
        )
        return list(result.scalars().all())

    async def delete_by_document_id(self, document_id: UUID) -> None:
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        await self.db.commit()