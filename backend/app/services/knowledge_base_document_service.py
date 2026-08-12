from uuid import UUID

from app.common.exceptions import NotFoundException
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository


class KnowledgeBaseDocumentService:
    def __init__(
        self,
        knowledge_base_repository: KnowledgeBaseRepository,
        document_repository: DocumentRepository,
    ):
        self.knowledge_base_repository = knowledge_base_repository
        self.document_repository = document_repository

    async def list_documents(
        self,
        *,
        knowledge_base_id: UUID,
        page: int,
        page_size: int,
        q: str | None,
        status: str | None,
        ingestion_status: str | None,
        is_latest: bool | None,
        source_type: str | None,
        sort_by: str,
        sort_order: str,
    ):
        knowledge_base = await self.knowledge_base_repository.find_by_id(
            knowledge_base_id
        )
        if knowledge_base is None:
            raise NotFoundException("KnowledgeBase")

        return await self.document_repository.search_by_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            page=page,
            page_size=page_size,
            q=q,
            status=status,
            ingestion_status=ingestion_status,
            is_latest=is_latest,
            source_type=source_type,
            sort_by=sort_by,
            sort_order=sort_order,
        )
