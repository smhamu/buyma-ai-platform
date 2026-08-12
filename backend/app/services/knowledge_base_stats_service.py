from uuid import UUID

from app.common.exceptions import NotFoundException
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.knowledge_base_stats_repository import (
    KnowledgeBaseStatsRepository,
)
from app.schemas.knowledge_base_stats import KnowledgeBaseStatsResponse


class KnowledgeBaseStatsService:
    def __init__(
        self,
        knowledge_base_repository: KnowledgeBaseRepository,
        stats_repository: KnowledgeBaseStatsRepository,
    ):
        self.knowledge_base_repository = knowledge_base_repository
        self.stats_repository = stats_repository

    async def get_stats(
        self,
        knowledge_base_id: UUID,
    ) -> KnowledgeBaseStatsResponse:
        knowledge_base = await self.knowledge_base_repository.find_by_id(
            knowledge_base_id
        )
        if knowledge_base is None:
            raise NotFoundException("KnowledgeBase")

        document_stats = await self.stats_repository.get_document_stats(
            knowledge_base_id
        )
        chunk_count = await self.stats_repository.count_chunks(knowledge_base_id)
        embedding_count = await self.stats_repository.count_embeddings(
            knowledge_base_id
        )

        return KnowledgeBaseStatsResponse(
            **document_stats,
            chunk_count=chunk_count,
            embedding_count=embedding_count,
        )
