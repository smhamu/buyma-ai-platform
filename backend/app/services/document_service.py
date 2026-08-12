from uuid import UUID

from fastapi import status

from app.common.exceptions import AppException
from app.services.base_service import BaseService


class DocumentService(BaseService):
    resource_name = "Document"

    async def delete(self, document_id: UUID):
        document = await self.get(document_id)

        if document.ingestion_status in {"pending", "processing"}:
            raise AppException(
                status_code=status.HTTP_409_CONFLICT,
                code="DOCUMENT_INGESTION_IN_PROGRESS",
                message=(
                    "Document cannot be deleted while ingestion is in progress."
                ),
            )

        await self.repository.delete(document)

        return {"id": str(document_id)}
