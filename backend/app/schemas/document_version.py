from uuid import UUID

from pydantic import BaseModel

from app.schemas.document import DocumentResponse


class DocumentVersionResponse(BaseModel):
    current: DocumentResponse
    previous: DocumentResponse | None


class DocumentVersionListResponse(BaseModel):
    document_id: UUID
    versions: list[DocumentResponse]
