from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.v1.embedding_jobs import enqueue_embedding_job
from app.common.exceptions import AppException


@pytest.mark.asyncio
async def test_enqueue_embedding_job_queues_pending_job():
    job_id = uuid4()
    job = SimpleNamespace(id=job_id, status="pending")
    authz = SimpleNamespace(
        require_embedding_job_access=AsyncMock(return_value=job)
    )

    with patch(
        "app.api.v1.embedding_jobs.run_embedding_job_task"
    ) as task:
        task.delay.return_value = SimpleNamespace(id="task-id")

        response = await enqueue_embedding_job(
            job_id=job_id,
            service=SimpleNamespace(),
            authz=authz,
            db=SimpleNamespace(),
            current_user=SimpleNamespace(),
        )

    authz.require_embedding_job_access.assert_awaited_once()
    task.delay.assert_called_once_with(str(job_id))
    assert response["success"] is True
    assert response["data"] == {
        "job_id": str(job_id),
        "task_id": "task-id",
        "status": "queued",
    }


@pytest.mark.asyncio
async def test_enqueue_embedding_job_queues_failed_job():
    job_id = uuid4()
    job = SimpleNamespace(id=job_id, status="failed")
    authz = SimpleNamespace(
        require_embedding_job_access=AsyncMock(return_value=job)
    )

    with patch(
        "app.api.v1.embedding_jobs.run_embedding_job_task"
    ) as task:
        task.delay.return_value = SimpleNamespace(id="task-id")

        response = await enqueue_embedding_job(
            job_id=job_id,
            service=SimpleNamespace(),
            authz=authz,
            db=SimpleNamespace(),
            current_user=SimpleNamespace(),
        )

    assert response["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_enqueue_embedding_job_rejects_completed_job():
    job_id = uuid4()
    job = SimpleNamespace(id=job_id, status="completed")
    authz = SimpleNamespace(
        require_embedding_job_access=AsyncMock(return_value=job)
    )

    with pytest.raises(AppException) as exc_info:
        await enqueue_embedding_job(
            job_id=job_id,
            service=SimpleNamespace(),
            authz=authz,
            db=SimpleNamespace(),
            current_user=SimpleNamespace(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "EMBEDDING_JOB_NOT_ENQUEUEABLE"
