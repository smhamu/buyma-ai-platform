from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.embedding import EmbeddingResponse
from app.services.embedding_service import EmbeddingService

router = APIRouter(tags=["Embeddings"])


def get_embedding_service(
    db: AsyncSession = Depends(get_db),
) -> EmbeddingService:
    return EmbeddingService(
        embedding_repository=EmbeddingRepository(db),
        job_repository=EmbeddingJobRepository(db),
        chunk_repository=DocumentChunkRepository(db),
        model_repository=EmbeddingModelRepository(db),
    )


@router.post("/embedding-jobs/{job_id}/run")
async def run_embedding_job(
    job_id: UUID,
    service: EmbeddingService = Depends(get_embedding_service),
    current_user: User = Depends(require_admin),
):
    embedding = await service.run_embedding_job(job_id)

    return success_response(
        data=EmbeddingResponse.model_validate(embedding),
        message="Embedding job completed successfully.",
    )


@router.get("/embeddings")
async def list_embeddings(
    service: EmbeddingService = Depends(get_embedding_service),
    current_user: User = Depends(get_current_user),
):
    embeddings = await service.list_embeddings()

    return success_response(
        data=[EmbeddingResponse.model_validate(embedding) for embedding in embeddings],
        message="Embeddings fetched successfully.",
    )


@router.get("/embeddings/{embedding_id}")
async def get_embedding(
    embedding_id: UUID,
    service: EmbeddingService = Depends(get_embedding_service),
    current_user: User = Depends(get_current_user),
):
    embedding = await service.get_embedding(embedding_id)

    return success_response(
        data=EmbeddingResponse.model_validate(embedding),
        message="Embedding fetched successfully.",
    )


@router.get("/chunks/{chunk_id}/embeddings")
async def list_chunk_embeddings(
    chunk_id: UUID,
    service: EmbeddingService = Depends(get_embedding_service),
    current_user: User = Depends(get_current_user),
):
    embeddings = await service.list_chunk_embeddings(chunk_id)

    return success_response(
        data=[EmbeddingResponse.model_validate(embedding) for embedding in embeddings],
        message="Chunk embeddings fetched successfully.",
    )