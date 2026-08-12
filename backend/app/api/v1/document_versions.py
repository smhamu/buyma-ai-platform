from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.exceptions import NotFoundException
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/documents", tags=["Document Versions"])


@router.get("/{document_id}/versions")
async def list_document_versions(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repository = DocumentRepository(db)
    document = await repository.find_by_id(document_id)

    if document is None:
        raise NotFoundException("Document")

    versions = await repository.find_versions_by_group(document.version_group_id)

    return success_response(
        data=[
            DocumentResponse.model_validate(version)
            for version in versions
        ],
        message="Document versions fetched successfully.",
    )
