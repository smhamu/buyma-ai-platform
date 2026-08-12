from typing import Literal

from pydantic import BaseModel

from app.schemas.document import DocumentResponse


class KnowledgeBaseDocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
    sort_by: str
    sort_order: Literal["asc", "desc"]
