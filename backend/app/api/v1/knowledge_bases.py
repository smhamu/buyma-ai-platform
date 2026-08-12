from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.document import DocumentResponse
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


def get_knowledge_base_service(
    db: AsyncSession = Depends(get_db),
) -> KnowledgeBaseService:
    return KnowledgeBaseService(KnowledgeBaseRepository(db))


@router.post("")
async def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    current_user: User = Depends(require_admin),
):
    knowledge_base = await service.create(payload)

    return success_response(
        data=KnowledgeBaseResponse.model_validate(knowledge_base),
        message="Knowledge base created successfully.",
    )


@router.get("")
async def list_knowledge_bases(
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    current_user: User = Depends(get_current_user),
):
    knowledge_bases = await service.list()

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
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    current_user: User = Depends(get_current_user),
):
    knowledge_base = await service.get(knowledge_base_id)

    return success_response(
        data=KnowledgeBaseResponse.model_validate(knowledge_base),
        message="Knowledge base fetched successfully.",
    )


@router.put("/{knowledge_base_id}")
async def update_knowledge_base(
    knowledge_base_id: UUID,
    payload: KnowledgeBaseUpdate,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    current_user: User = Depends(require_admin),
):
    knowledge_base = await service.update(knowledge_base_id, payload)

    return success_response(
        data=KnowledgeBaseResponse.model_validate(knowledge_base),
        message="Knowledge base updated successfully.",
    )


@router.delete("/{knowledge_base_id}")
async def delete_knowledge_base(
    knowledge_base_id: UUID,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    current_user: User = Depends(require_admin),
):
    result = await service.delete(knowledge_base_id)

    return success_response(
        data=result,
        message="Knowledge base deleted successfully.",
    )


@router.get("/{knowledge_base_id}/documents")
async def list_knowledge_base_documents(
    knowledge_base_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: KnowledgeBaseService = Depends(get_knowledge_base_service),
    current_user: User = Depends(get_current_user),
):
    await service.get(knowledge_base_id)
    document_repository = DocumentRepository(db)
    documents = await document_repository.find_by_knowledge_base_id(
        knowledge_base_id
    )

    return success_response(
        data=[
            DocumentResponse.model_validate(document)
            for document in documents
        ],
        message="Knowledge base documents fetched successfully.",
    )
