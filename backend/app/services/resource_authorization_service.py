from uuid import UUID

from app.common.exceptions import NotFoundException
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository


class ResourceAuthorizationService:
    def __init__(
        self,
        knowledge_base_repository: KnowledgeBaseRepository,
        document_repository: DocumentRepository,
    ):
        self.knowledge_base_repository = knowledge_base_repository
        self.document_repository = document_repository

    def _is_admin(self, user: User) -> bool:
        return user.role == "admin"

    async def require_knowledge_base_access(
        self,
        knowledge_base_id: UUID,
        current_user: User,
    ):
        if self._is_admin(current_user):
            knowledge_base = await self.knowledge_base_repository.find_by_id(
                knowledge_base_id
            )
        else:
            knowledge_base = await self.knowledge_base_repository.find_by_id_and_owner(
                knowledge_base_id,
                current_user.id,
            )

        if knowledge_base is None:
            raise NotFoundException("KnowledgeBase")

        return knowledge_base

    async def require_document_access(
        self,
        document_id: UUID,
        current_user: User,
    ):
        document = await self.document_repository.find_by_id(document_id)

        if document is None:
            raise NotFoundException("Document")

        if self._is_admin(current_user):
            return document

        if document.knowledge_base_id is None:
            raise NotFoundException("Document")

        knowledge_base = await self.knowledge_base_repository.find_by_id_and_owner(
            document.knowledge_base_id,
            current_user.id,
        )

        if knowledge_base is None:
            raise NotFoundException("Document")

        return document

    async def require_embedding_job_access(
        self,
        job_id: UUID,
        current_user: User,
        job_repository: EmbeddingJobRepository,
    ):
        job = await job_repository.find_by_id(job_id)

        if job is None:
            raise NotFoundException("EmbeddingJob")

        await self.require_document_access(job.document_id, current_user)

        return job
