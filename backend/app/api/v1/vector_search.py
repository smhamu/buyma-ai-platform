from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.vector_search import VectorSearchRequest, VectorSearchResult
from app.services.vector_search_service import VectorSearchService

router = APIRouter(prefix="/search", tags=["Vector Search"])


def get_vector_search_service(
    db: AsyncSession = Depends(get_db),
) -> VectorSearchService:
    return VectorSearchService(
        embedding_repository=EmbeddingRepository(db),
        model_repository=EmbeddingModelRepository(db),
    )


@router.post("/vector")
async def vector_search(
    payload: VectorSearchRequest,
    service: VectorSearchService = Depends(get_vector_search_service),
    current_user: User = Depends(get_current_user),
):
    results = await service.search(payload)

    return success_response(
        data=[
            VectorSearchResult(
                embedding_id=row.embedding_id,
                document_id=row.document_id,
                chunk_id=row.chunk_id,
                content=row.content,
                distance=float(row.distance),
            )
            for row in results
        ],
        message="Vector search completed successfully.",
    )