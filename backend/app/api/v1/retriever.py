from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.retriever import RetrieverRequest
from app.services.retriever_service import RetrieverService
from app.services.vector_search_service import VectorSearchService

router = APIRouter(prefix="/retriever", tags=["Retriever"])


def get_retriever_service(
    db: AsyncSession = Depends(get_db),
) -> RetrieverService:
    vector_search_service = VectorSearchService(
        embedding_repository=EmbeddingRepository(db),
        model_repository=EmbeddingModelRepository(db),
    )
    return RetrieverService(vector_search_service=vector_search_service)


@router.post("/search")
async def retrieve(
    payload: RetrieverRequest,
    service: RetrieverService = Depends(get_retriever_service),
    current_user: User = Depends(get_current_user),
):
    result = await service.retrieve(payload)

    return success_response(
        data=result.model_dump(),
        message="Context retrieved successfully.",
    )
