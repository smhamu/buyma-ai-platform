from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.document_chunk import DocumentChunkResponse
from app.services.document_chunk_service import DocumentChunkService

router = APIRouter(prefix="/documents", tags=["Document Chunks"])


def get_document_chunk_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentChunkService:
    chunk_repository = DocumentChunkRepository(db)
    document_repository = DocumentRepository(db)

    return DocumentChunkService(
        chunk_repository=chunk_repository,
        document_repository=document_repository,
    )


@router.post("/{document_id}/chunks")
async def generate_document_chunks(
    document_id: UUID,
    service: DocumentChunkService = Depends(get_document_chunk_service),
    current_user: User = Depends(require_admin),
):
    chunks = await service.generate_chunks(document_id)

    return success_response(
        data=[DocumentChunkResponse.model_validate(chunk) for chunk in chunks],
        message="Document chunks generated successfully.",
    )


@router.get("/{document_id}/chunks")
async def list_document_chunks(
    document_id: UUID,
    service: DocumentChunkService = Depends(get_document_chunk_service),
    current_user: User = Depends(get_current_user),
):
    chunks = await service.list_chunks(document_id)

    return success_response(
        data=[DocumentChunkResponse.model_validate(chunk) for chunk in chunks],
        message="Document chunks fetched successfully.",
    )