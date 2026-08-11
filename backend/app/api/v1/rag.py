from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.rag import RAGQueryRequest
from app.services.prompt_builder_service import PromptBuilderService
from app.services.rag_service import RAGService
from app.services.retriever_service import RetrieverService
from app.services.vector_search_service import VectorSearchService

router = APIRouter(prefix="/rag", tags=["RAG"])


def get_rag_service(
    db: AsyncSession = Depends(get_db),
) -> RAGService:
    vector_search_service = VectorSearchService(
        embedding_repository=EmbeddingRepository(db),
        model_repository=EmbeddingModelRepository(db),
    )
    retriever_service = RetrieverService(
        vector_search_service=vector_search_service,
    )
    prompt_builder_service = PromptBuilderService(
        retriever_service=retriever_service,
    )
    return RAGService(prompt_builder_service=prompt_builder_service)


@router.post("/query")
async def rag_query(
    payload: RAGQueryRequest,
    service: RAGService = Depends(get_rag_service),
    current_user: User = Depends(get_current_user),
):
    result = await service.query(payload)

    return success_response(
        data=result.model_dump(),
        message="RAG query completed successfully.",
    )
