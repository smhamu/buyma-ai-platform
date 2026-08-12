from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.schemas.document import DocumentResponse
from app.schemas.document_chunk import DocumentChunkResponse
from app.schemas.document_ingestion import (
    DocumentIngestionRequest,
    DocumentIngestionResponse,
)
from app.schemas.embedding_job import EmbeddingJobResponse
from app.services.document_ingestion_service import DocumentIngestionService

router = APIRouter(prefix="/documents", tags=["Document Ingestion"])


def get_document_ingestion_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentIngestionService:
    return DocumentIngestionService(
        document_repository=DocumentRepository(db),
        chunk_repository=DocumentChunkRepository(db),
        embedding_job_repository=EmbeddingJobRepository(db),
        embedding_model_repository=EmbeddingModelRepository(db),
    )


@router.post("/ingest")
async def ingest_document(
    payload: DocumentIngestionRequest,
    service: DocumentIngestionService = Depends(get_document_ingestion_service),
    current_user: User = Depends(require_admin),
):
    result = await service.ingest(payload)

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
    )

    return success_response(
        data=response.model_dump(),
        message="Document ingestion completed successfully.",
    )
