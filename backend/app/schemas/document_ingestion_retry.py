from uuid import UUID

from pydantic import BaseModel


class DocumentIngestionRetryResponse(BaseModel):
    document_id: UUID
    retried_job_ids: list[UUID]
    task_ids: list[str]
    retried_count: int
