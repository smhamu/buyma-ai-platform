from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.prompt_builder import PromptBuildRequest
from app.services.prompt_builder_service import PromptBuilderService
from app.services.retriever_service import RetrieverService
from app.services.vector_search_service import VectorSearchService

router = APIRouter(prefix="/prompt", tags=["Prompt Builder"])


def get_prompt_builder_service(
    db: AsyncSession = Depends(get_db),
) -> PromptBuilderService:
    vector_search_service = VectorSearchService(
        embedding_repository=EmbeddingRepository(db),
        model_repository=EmbeddingModelRepository(db),
    )
    retriever_service = RetrieverService(
        vector_search_service=vector_search_service,
    )
    return PromptBuilderService(retriever_service=retriever_service)


@router.post("/build")
async def build_prompt(
    payload: PromptBuildRequest,
    service: PromptBuilderService = Depends(get_prompt_builder_service),
    current_user: User = Depends(get_current_user),
):
    result = await service.build(payload)

    return success_response(
        data=result.model_dump(),
        message="Prompt built successfully.",
    )
