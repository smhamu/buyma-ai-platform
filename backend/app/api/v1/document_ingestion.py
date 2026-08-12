from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.document import DocumentResponse
from app.schemas.document_chunk import DocumentChunkResponse
from app.schemas.document_ingestion import (
    DocumentIngestionRequest,
    DocumentIngestionResponse,
)
from app.schemas.document_file_ingestion import DocumentFileIngestionResponse
from app.schemas.document_ingestion_retry import DocumentIngestionRetryResponse
from app.schemas.embedding_job import EmbeddingJobResponse
from app.services.document_ingestion_retry_service import (
    DocumentIngestionRetryService,
)
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.document_file_ingestion_service import (
    DocumentFileIngestionService,
)
from app.services.embedding_queue_service import EmbeddingQueueService

router = APIRouter(prefix="/documents", tags=["Document Ingestion"])


def get_document_ingestion_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentIngestionService:
    return DocumentIngestionService(
        document_repository=DocumentRepository(db),
        chunk_repository=DocumentChunkRepository(db),
        embedding_job_repository=EmbeddingJobRepository(db),
        embedding_model_repository=EmbeddingModelRepository(db),
        knowledge_base_repository=KnowledgeBaseRepository(db),
    )


def get_embedding_queue_service() -> EmbeddingQueueService:
    return EmbeddingQueueService()


def get_document_ingestion_retry_service(
    db: AsyncSession = Depends(get_db),
    queue_service: EmbeddingQueueService = Depends(get_embedding_queue_service),
) -> DocumentIngestionRetryService:
    return DocumentIngestionRetryService(
        document_repository=DocumentRepository(db),
        embedding_job_repository=EmbeddingJobRepository(db),
        queue_service=queue_service,
    )


def get_document_file_ingestion_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentFileIngestionService:
    document_repository = DocumentRepository(db)
    ingestion_service = DocumentIngestionService(
        document_repository=document_repository,
        chunk_repository=DocumentChunkRepository(db),
        embedding_job_repository=EmbeddingJobRepository(db),
        embedding_model_repository=EmbeddingModelRepository(db),
        knowledge_base_repository=KnowledgeBaseRepository(db),
    )
    return DocumentFileIngestionService(
        ingestion_service=ingestion_service,
        document_repository=document_repository,
    )


@router.post("/ingest")
async def ingest_document(
    payload: DocumentIngestionRequest,
    service: DocumentIngestionService = Depends(get_document_ingestion_service),
    queue_service: EmbeddingQueueService = Depends(get_embedding_queue_service),
    current_user: User = Depends(require_admin),
):
    result = await service.ingest(payload)
    task_ids: list[str] = []

    if payload.auto_enqueue:
        for job in result["embedding_jobs"]:
            task_ids.append(queue_service.enqueue(job.id))

    response = DocumentIngestionResponse(
        document=DocumentResponse.model_validate(result["document"]),
        chunks=[
            DocumentChunkResponse.model_validate(chunk)
            for chunk in result["chunks"]
        ],
        embedding_jobs=[
            EmbeddingJobResponse.model_validate(job)
            for job in result["embedding_jobs"]
        ],
        task_ids=task_ids,
    )

    return success_response(
        data=response.model_dump(),
        message="Document ingestion completed successfully.",
    )


@router.post("/ingest-file")
async def ingest_document_file(
    file: UploadFile = File(...),
    embedding_model_id: UUID = Form(...),
    knowledge_base_id: UUID | None = Form(default=None),
    chunk_size: int = Form(default=500, ge=100, le=5000),
    auto_enqueue: bool = Form(default=True),
    service: DocumentFileIngestionService = Depends(
        get_document_file_ingestion_service
    ),
    queue_service: EmbeddingQueueService = Depends(get_embedding_queue_service),
    current_user: User = Depends(require_admin),
):
    file_content = await file.read()
    result = await service.ingest_file(
        filename=file.filename or "document",
        file_content=file_content,
        embedding_model_id=embedding_model_id,
        mime_type=file.content_type,
        knowledge_base_id=knowledge_base_id,
        chunk_size=chunk_size,
    )

    task_ids: list[str] = []
    if auto_enqueue:
        for job in result["embedding_jobs"]:
            task_ids.append(queue_service.enqueue(job.id))

    response = DocumentFileIngestionResponse(
        filename=result["filename"],
        file_size=result["file_size"],
        document=DocumentResponse.model_validate(result["document"]),
        chunks=[
            DocumentChunkResponse.model_validate(chunk)
            for chunk in result["chunks"]
        ],
        embedding_jobs=[
            EmbeddingJobResponse.model_validate(job)
            for job in result["embedding_jobs"]
        ],
        task_ids=task_ids,
    )

    return success_response(
        data=response.model_dump(),
        message="Document file ingestion completed successfully.",
    )


@router.post(
    "/{document_id}/retry-ingestion",
    response_model=dict,
)
async def retry_document_ingestion(
    document_id: UUID,
    service: DocumentIngestionRetryService = Depends(
        get_document_ingestion_retry_service
    ),
    current_user: User = Depends(require_admin),
):
    result = await service.retry(document_id)
    response = DocumentIngestionRetryResponse(**result)

    return success_response(
        data=response.model_dump(),
        message="Document ingestion retry started successfully.",
    )
