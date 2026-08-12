from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.resource_authorization_service import ResourceAuthorizationService


def get_resource_authorization_service(
    db: AsyncSession = Depends(get_db),
) -> ResourceAuthorizationService:
    return ResourceAuthorizationService(
        knowledge_base_repository=KnowledgeBaseRepository(db),
        document_repository=DocumentRepository(db),
    )
