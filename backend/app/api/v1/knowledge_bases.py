from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import get_resource_authorization_service
from app.api.deps import get_current_user, require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.repositories.knowledge_base_stats_repository import (
    KnowledgeBaseStatsRepository,
)
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.document import DocumentResponse
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.schemas.knowledge_base_stats import KnowledgeBaseStatsResponse
from app.schemas.knowledge_base_document import KnowledgeBaseDocumentListResponse
from app.services.knowledge_base_document_service import KnowledgeBaseDocumentService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.knowledge_base_stats_service import KnowledgeBaseStatsService
from app.services.resource_authorization_service import ResourceAuthorizationService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


def get_knowledge_base_service(
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseService:
    return KnowledgeBaseService(KnowledgeBaseRepository(db))


def get_knowledge_base_document_service(
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseDocumentService:
    return KnowledgeBaseDocumentService(
        knowledge_base_repository=KnowledgeBaseRepository(db),
        document_repository=DocumentRepository(db),
    )


def get_knowledge_base_stats_service(
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseStatsService:
    return KnowledgeBaseStatsService(
        knowledge_base_repository=KnowledgeBaseRepository(db),
        stats_repository=KnowledgeBaseStatsRepository(db),
    )


@router.post("")
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = await service.create(
        {
            "owner_user_id": current_user.id,
            "name": payload.name,
            "description": payload.description,
            "is_active": payload.is_active,
        }
    )

    return success_response(
        data=KnowledgeBaseResponse.model_validate(knowledge_base),
        message="Knowledge base created successfully.",
    )


@router.get("")
async def list_knowledge_bases(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "admin":
        knowledge_bases = await service.list()
    else:
        knowledge_bases = await service.repository.find_all_by_owner(current_user.id)

    return success_response(
        data=[
            KnowledgeBaseResponse.model_validate(knowledge_base)
            for knowledge_base in knowledge_bases
        ],
        message="Knowledge bases fetched successfully.",
    )


@router.get("/{knowledge_base_id}")
async def get_knowledge_base(
    knowledge_base_id: UUID,
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = await authz.require_knowledge_base_access(
        knowledge_base_id,
        current_user,
    )

    return success_response(
        data=KnowledgeBaseResponse.model_validate(knowledge_base),
        message="Knowledge base fetched successfully.",
    )


@router.put("/{knowledge_base_id}")
async def update_knowledge_base(
    knowledge_base_id: UUID,
    payload: KnowledgeBaseUpdate,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    await authz.require_knowledge_base_access(knowledge_base_id, current_user)
    knowledge_base = await service.update(knowledge_base_id, payload)

    return success_response(
        data=KnowledgeBaseResponse.model_validate(knowledge_base),
        message="Knowledge base updated successfully.",
    )


@router.delete("/{knowledge_base_id}")
async def delete_knowledge_base(
    knowledge_base_id: UUID,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    await authz.require_knowledge_base_access(knowledge_base_id, current_user)
    result = await service.delete(knowledge_base_id)

    return success_response(
        data=result,
        message="Knowledge base deleted successfully.",
    )


@router.get(
    "/{knowledge_base_id}/stats",
    response_model=SuccessResponse[KnowledgeBaseStatsResponse],
    responses={404: {"model": ErrorResponse}},
    summary="Get Knowledge Base statistics",
    description=(
        "Returns document, chunk, embedding, and ingestion status counts "
        "for the specified Knowledge Base."
    ),
)
async def get_knowledge_base_stats(
    knowledge_base_id: UUID,
    service: KnowledgeBaseStatsService = Depends(get_knowledge_base_stats_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    await authz.require_knowledge_base_access(knowledge_base_id, current_user)
    stats = await service.get_stats(knowledge_base_id)

    return success_response(
        data=stats.model_dump(),
        message="Knowledge base stats fetched successfully.",
    )


@router.get("/{knowledge_base_id}/documents")
async def list_knowledge_base_documents(
    knowledge_base_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, min_length=1, max_length=255),
    status: str | None = Query(default=None),
    ingestion_status: str | None = Query(default=None),
    is_latest: bool | None = Query(default=True),
    source_type: str | None = Query(default=None),
    sort_by: Literal[
        "created_at",
        "updated_at",
        "title",
        "version",
        "ingestion_status",
    ] = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    service: KnowledgeBaseDocumentService = Depends(
        get_knowledge_base_document_service
    ),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    await authz.require_knowledge_base_access(knowledge_base_id, current_user)
    result = await service.list_documents(
        knowledge_base_id=knowledge_base_id,
        page=page,
        page_size=page_size,
        q=q,
        status=status,
        ingestion_status=ingestion_status,
        is_latest=is_latest,
        source_type=source_type,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    response = KnowledgeBaseDocumentListResponse(
        items=[
            DocumentResponse.model_validate(document)
            for document in result["items"]
        ],
        page=page,
        page_size=page_size,
        total=result["total"],
        total_pages=result["total_pages"],
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return success_response(
        data=response.model_dump(),
        message="Knowledge base documents fetched successfully.",
    )
