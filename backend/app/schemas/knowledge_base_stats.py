from pydantic import BaseModel


class KnowledgeBaseStatsResponse(BaseModel):
    document_count: int
    latest_document_count: int
    ready_count: int
    pending_count: int
    processing_count: int
    failed_count: int
    chunk_count: int
    embedding_count: int
