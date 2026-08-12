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
from app.schemas.vector_search import VectorSearchRequest, VectorSearchResult
from app.services.resource_authorization_service import ResourceAuthorizationService
from app.services.vector_search_service import VectorSearchService

router = APIRouter(prefix="/search", tags=["Vector Search"])


def get_vector_search_service(
    db: AsyncSession = Depends(get_db),
) -> VectorSearchService:
    return VectorSearchService(
        embedding_repository=EmbeddingRepository(db),
        model_repository=EmbeddingModelRepository(db),
    )


@router.post(
    "/vector",
    response_model=SuccessResponse[list[VectorSearchResult]],
    responses={422: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Run vector similarity search",
    description=(
        "Performs vector similarity search on embeddings in the specified "
        "Knowledge Base and returns matching chunks."
    ),
)
async def vector_search(
    payload: VectorSearchRequest,
    service: VectorSearchService = Depends(get_vector_search_service),
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
