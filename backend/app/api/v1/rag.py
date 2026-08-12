from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import get_resource_authorization_service
from app.api.deps import get_current_user
from app.common.exceptions import AppException
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.embedding_repository import EmbeddingRepository
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.prompt_builder_service import PromptBuilderService
from app.services.rag_service import RAGService
from app.services.resource_authorization_service import ResourceAuthorizationService
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


@router.post(
    "/query",
    response_model=SuccessResponse[RAGQueryResponse],
    responses={422: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Run RAG query",
    description=(
        "Runs retrieval-augmented generation against the specified "
        "Knowledge Base and returns answer, context, and source chunks."
    ),
)
async def rag_query(
    payload: RAGQueryRequest,
    service: RAGService = Depends(get_rag_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    if payload.knowledge_base_id is None:
        if current_user.role != "admin":
            raise AppException(
                status_code=422,
                code="KNOWLEDGE_BASE_REQUIRED",
                message="knowledge_base_id is required.",
            )
    else:
        await authz.require_knowledge_base_access(
            payload.knowledge_base_id,
            current_user,
        )
    result = await service.query(payload)

    return success_response(
        data=result.model_dump(),
        message="RAG query completed successfully.",
    )
