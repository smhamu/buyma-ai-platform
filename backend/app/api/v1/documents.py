from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import get_resource_authorization_service
from app.api.deps import get_current_user
from app.common.exceptions import AppException
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services.document_service import DocumentService
from app.services.resource_authorization_service import ResourceAuthorizationService

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_service(
    db: AsyncSession = Depends(get_db),
) -> DocumentService:
    repository = DocumentRepository(db)
    return DocumentService(repository)


@router.post("")
async def create_document(
    payload: DocumentCreate,
    service: DocumentService = Depends(get_document_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    if payload.knowledge_base_id is not None:
        await authz.require_knowledge_base_access(
            payload.knowledge_base_id,
            current_user,
        )
    document = await service.create(payload)

    return success_response(
        data=DocumentResponse.model_validate(document),
        message="Document created successfully.",
    )


@router.get("")
async def list_documents(
    service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise AppException(
            status_code=403,
            code="ADMIN_REQUIRED",
            message="Admin permission required.",
        )
    documents = await service.list()

    return success_response(
        data=[DocumentResponse.model_validate(document) for document in documents],
        message="Documents fetched successfully.",
    )


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    document = await authz.require_document_access(document_id, current_user)

    return success_response(
        data=DocumentResponse.model_validate(document),
        message="Document fetched successfully.",
    )


@router.put("/{document_id}")
async def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    service: DocumentService = Depends(get_document_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    await authz.require_document_access(document_id, current_user)
    if payload.knowledge_base_id is not None:
        await authz.require_knowledge_base_access(
            payload.knowledge_base_id,
            current_user,
        )
    document = await service.update(document_id, payload)

    return success_response(
        data=DocumentResponse.model_validate(document),
        message="Document updated successfully.",
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(get_document_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    await authz.require_document_access(document_id, current_user)
    result = await service.delete(document_id)

    return success_response(
        data=result,
        message="Document deleted successfully.",
    )
