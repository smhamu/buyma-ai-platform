from uuid import UUID

from pydantic import BaseModel


class DocumentVersionDiffLine(BaseModel):
    type: str
    content: str


class DocumentVersionDiffResponse(BaseModel):
    base_document_id: UUID
    base_version: int
    compare_document_id: UUID
    compare_version: int
    lines: list[DocumentVersionDiffLine]
    added_count: int
    removed_count: int
    unchanged_count: int
    has_changes: bool
