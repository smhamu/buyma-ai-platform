from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.embedding import Embedding


class KnowledgeBaseStatsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_document_stats(
        self,
        knowledge_base_id: UUID,
    ) -> dict[str, int]:
        result = await self.db.execute(
            select(
                func.count(Document.id).label("document_count"),
                func.count(Document.id)
                .filter(Document.is_latest.is_(True))
                .label("latest_document_count"),
                func.count(Document.id)
                .filter(
                    Document.is_latest.is_(True),
                    Document.ingestion_status == "ready",
                )
                .label("ready_count"),
                func.count(Document.id)
                .filter(
                    Document.is_latest.is_(True),
                    Document.ingestion_status == "pending",
                )
                .label("pending_count"),
                func.count(Document.id)
                .filter(
                    Document.is_latest.is_(True),
                    Document.ingestion_status == "processing",
                )
                .label("processing_count"),
                func.count(Document.id)
                .filter(
                    Document.is_latest.is_(True),
                    Document.ingestion_status == "failed",
                )
                .label("failed_count"),
            ).where(Document.knowledge_base_id == knowledge_base_id)
        )
        row = result.one()

        return {
            "document_count": int(row.document_count),
            "latest_document_count": int(row.latest_document_count),
            "ready_count": int(row.ready_count),
            "pending_count": int(row.pending_count),
            "processing_count": int(row.processing_count),
            "failed_count": int(row.failed_count),
        }

    async def count_chunks(
        self,
        knowledge_base_id: UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(DocumentChunk.id))
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.is_latest.is_(True),
            )
        )
        return int(result.scalar_one())

    async def count_embeddings(
        self,
        knowledge_base_id: UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Embedding.id))
            .join(Document, Document.id == Embedding.document_id)
            .where(
                Document.knowledge_base_id == knowledge_base_id,
                Document.is_latest.is_(True),
                Embedding.status == "active",
            )
        )
        return int(result.scalar_one())
