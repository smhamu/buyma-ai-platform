from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.common.exceptions import NotFoundException
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.document import DocumentResponse
from app.schemas.document_version_diff import DocumentVersionDiffResponse
from app.schemas.document_version_rollback import DocumentVersionRollbackResponse
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.document_version_diff_service import DocumentVersionDiffService
from app.services.document_version_rollback_service import (
    DocumentVersionRollbackService,
)
from app.services.embedding_queue_service import EmbeddingQueueService

router = APIRouter(prefix="/documents", tags=["Document Versions"])


def get_document_version_rollback_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentVersionRollbackService:
    document_repository = DocumentRepository(db)
    embedding_job_repository = EmbeddingJobRepository(db)
    ingestion_service = DocumentIngestionService(
        db=db,
        document_repository=document_repository,
        chunk_repository=DocumentChunkRepository(db),
        embedding_job_repository=embedding_job_repository,
        embedding_model_repository=EmbeddingModelRepository(db),
        knowledge_base_repository=KnowledgeBaseRepository(db),
    )
    return DocumentVersionRollbackService(
        db=db,
        document_repository=document_repository,
        embedding_job_repository=embedding_job_repository,
        ingestion_service=ingestion_service,
    )


def get_document_version_diff_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentVersionDiffService:
    return DocumentVersionDiffService(
        document_repository=DocumentRepository(db),
    )


@router.get("/{document_id}/versions")
async def list_document_versions(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = DocumentRepository(db)
    document = await repository.find_by_id(document_id)

    if document is None:
        raise NotFoundException("Document")

    versions = await repository.find_versions_by_group(document.version_group_id)

    return success_response(
        data=[
            DocumentResponse.model_validate(version)
            for version in versions
        ],
        message="Document versions fetched successfully.",
    )


@router.get("/{document_id}/versions/{compare_document_id}/diff")
async def compare_document_versions(
    document_id: UUID,
    compare_document_id: UUID,
    service: DocumentVersionDiffService = Depends(get_document_version_diff_service),
    current_user: User = Depends(get_current_user),
):
    result = await service.compare(
        base_document_id=document_id,
        compare_document_id=compare_document_id,
    )
    response = DocumentVersionDiffResponse.model_validate(result)

    return success_response(
        data=response.model_dump(),
        message="Document version diff fetched successfully.",
    )


@router.post("/{document_id}/restore")
async def restore_document_version(
    document_id: UUID,
    service: DocumentVersionRollbackService = Depends(
        get_document_version_rollback_service
    ),
    queue_service: EmbeddingQueueService = Depends(EmbeddingQueueService),
    current_user: User = Depends(require_admin),
):
    result = await service.restore(document_id)
    task_ids = [
        queue_service.enqueue(job.id)
        for job in result["embedding_jobs"]
    ]
    response = DocumentVersionRollbackResponse(
        restored_from_document_id=result["restored_from_document_id"],
        restored_from_version=result["restored_from_version"],
        new_document=DocumentResponse.model_validate(result["new_document"]),
        task_ids=task_ids,
    )

    return success_response(
        data=response.model_dump(),
        message="Document version restored successfully.",
    )
