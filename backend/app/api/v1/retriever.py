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
from app.schemas.retriever import RetrieverRequest, RetrieverResponse
from app.services.resource_authorization_service import ResourceAuthorizationService
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


@router.post(
    "/search",
    response_model=SuccessResponse[RetrieverResponse],
    responses={422: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Retrieve context chunks",
    description=(
        "Searches the specified Knowledge Base and returns retrieved chunks "
        "plus combined context for downstream prompt construction."
    ),
)
async def retrieve(
    payload: RetrieverRequest,
    service: RetrieverService = Depends(get_retriever_service),
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
    result = await service.retrieve(payload)

    return success_response(
        data=result.model_dump(),
        message="Context retrieved successfully.",
    )
