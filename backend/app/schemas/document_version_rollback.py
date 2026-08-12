from uuid import UUID

from pydantic import BaseModel

from app.schemas.document import DocumentResponse


class DocumentVersionRollbackResponse(BaseModel):
    restored_from_document_id: UUID
    restored_from_version: int
    new_document: DocumentResponse
    task_ids: list[str]
