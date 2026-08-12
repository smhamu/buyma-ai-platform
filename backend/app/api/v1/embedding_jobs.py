from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.authz import get_resource_authorization_service
from app.api.deps import get_current_user, require_admin
from app.common.exceptions import AppException
from app.common.responses import success_response
from app.core.database import get_db
from app.models.user import User
from app.repositories.document_chunk_repository import DocumentChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.embedding_job_repository import EmbeddingJobRepository
from app.repositories.embedding_model_repository import EmbeddingModelRepository
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.schemas.embedding_job import EmbeddingJobGenerateRequest, EmbeddingJobResponse
from app.services.embedding_job_service import EmbeddingJobService
from app.services.resource_authorization_service import ResourceAuthorizationService
from app.workers.embedding_tasks import run_embedding_job_task

router = APIRouter(tags=["Embedding Jobs"])


def get_embedding_job_service(
    db: AsyncSession = Depends(get_db),
) -> EmbeddingJobService:
    return EmbeddingJobService(
        job_repository=EmbeddingJobRepository(db),
        document_repository=DocumentRepository(db),
        chunk_repository=DocumentChunkRepository(db),
        model_repository=EmbeddingModelRepository(db),
    )


@router.post("/documents/{document_id}/embedding-jobs")
async def generate_embedding_jobs(
    document_id: UUID,
    payload: EmbeddingJobGenerateRequest,
    service: EmbeddingJobService = Depends(get_embedding_job_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(require_admin),
):
    await authz.require_document_access(document_id, current_user)
    jobs = await service.generate_jobs_for_document(
        document_id=document_id,
        embedding_model_id=payload.embedding_model_id,
    )

    return success_response(
        data=[EmbeddingJobResponse.model_validate(job) for job in jobs],
        message="Embedding jobs generated successfully.",
    )


@router.get("/documents/{document_id}/embedding-jobs")
async def list_document_embedding_jobs(
    document_id: UUID,
    service: EmbeddingJobService = Depends(get_embedding_job_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    current_user: User = Depends(get_current_user),
):
    await authz.require_document_access(document_id, current_user)
    jobs = await service.list_document_jobs(document_id)

    return success_response(
        data=[EmbeddingJobResponse.model_validate(job) for job in jobs],
        message="Document embedding jobs fetched successfully.",
    )


@router.get("/embedding-jobs")
async def list_embedding_jobs(
    service: EmbeddingJobService = Depends(get_embedding_job_service),
    current_user: User = Depends(require_admin),
):
    jobs = await service.list_jobs()

    return success_response(
        data=[EmbeddingJobResponse.model_validate(job) for job in jobs],
        message="Embedding jobs fetched successfully.",
    )


@router.get("/embedding-jobs/{job_id}")
async def get_embedding_job(
    job_id: UUID,
    service: EmbeddingJobService = Depends(get_embedding_job_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await authz.require_embedding_job_access(
        job_id,
        current_user,
        EmbeddingJobRepository(db),
    )

    return success_response(
        data=EmbeddingJobResponse.model_validate(job),
        message="Embedding job fetched successfully.",
    )


@router.post("/embedding-jobs/{job_id}/enqueue")
async def enqueue_embedding_job(
    job_id: UUID,
    service: EmbeddingJobService = Depends(get_embedding_job_service),
    authz: ResourceAuthorizationService = Depends(get_resource_authorization_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    job = await authz.require_embedding_job_access(
        job_id,
        current_user,
        EmbeddingJobRepository(db),
    )

    if job.status not in {"pending", "failed"}:
        raise AppException(
            status_code=409,
            code="EMBEDDING_JOB_NOT_ENQUEUEABLE",
            message=(
                "Embedding job cannot be enqueued "
                f"from status '{job.status}'."
            ),
        )

    task = run_embedding_job_task.delay(str(job.id))

    return success_response(
        data={
            "job_id": str(job.id),
            "task_id": task.id,
            "status": "queued",
        },
        message="Embedding job queued successfully.",
    )
