from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.embedding_job_recovery_service import EmbeddingJobRecoveryService


class FakeDb:
    def __init__(self):
        self.commit_count = 0
        self.rollback_count = 0

    def in_transaction(self):
        return False

    def begin(self):
        return FakeTransaction()

    async def commit(self):
        self.commit_count += 1

    async def rollback(self):
        self.rollback_count += 1


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeJobRepository:
    def __init__(self, jobs, recoverable_ids=None):
        self.jobs = jobs
        self.recoverable_ids = recoverable_ids or {job.id for job in jobs}
        self.find_calls = []
        self.reset_calls = []

    async def find_stale_processing_jobs(self, stale_before, limit):
        self.find_calls.append({"stale_before": stale_before, "limit": limit})
        return self.jobs[:limit]

    async def reset_stale_job_to_pending(self, job_id, stale_before):
        self.reset_calls.append({"job_id": job_id, "stale_before": stale_before})
        return job_id in self.recoverable_ids


class FakeStatusService:
    def __init__(self):
        self.refreshed_document_ids = []

    async def refresh_status_in_transaction(self, document_id):
        self.refreshed_document_ids.append(document_id)


def make_job(**overrides):
    data = {
        "id": uuid4(),
        "document_id": uuid4(),
        "status": "processing",
        "error_message": None,
        "updated_at": datetime.now(timezone.utc) - timedelta(minutes=20),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.asyncio
async def test_recover_stale_jobs_resets_jobs_and_refreshes_documents():
    document_id = uuid4()
    jobs = [
        make_job(document_id=document_id),
        make_job(document_id=document_id),
    ]
    repository = FakeJobRepository(jobs)
    service = EmbeddingJobRecoveryService(
        db=FakeDb(),
        job_repository=repository,
        document_repository=SimpleNamespace(),
    )
    status_service = FakeStatusService()
    service.status_service = status_service

    recovered = await service.recover_stale_jobs(stale_minutes=10, limit=100)

    assert recovered == jobs
    assert [job.status for job in jobs] == ["pending", "pending"]
    assert [job.error_message for job in jobs] == [
        "Recovered from stale processing state.",
        "Recovered from stale processing state.",
    ]
    assert status_service.refreshed_document_ids == [document_id]
    assert [call["job_id"] for call in repository.reset_calls] == [
        job.id for job in jobs
    ]


@pytest.mark.asyncio
async def test_recover_stale_jobs_skips_jobs_that_were_already_recovered():
    first = make_job()
    second = make_job()
    repository = FakeJobRepository([first, second], recoverable_ids={first.id})
    service = EmbeddingJobRecoveryService(
        db=FakeDb(),
        job_repository=repository,
        document_repository=SimpleNamespace(),
    )
    status_service = FakeStatusService()
    service.status_service = status_service

    recovered = await service.recover_stale_jobs(stale_minutes=10, limit=100)

    assert recovered == [first]
    assert first.status == "pending"
    assert second.status == "processing"
    assert status_service.refreshed_document_ids == [first.document_id]


@pytest.mark.asyncio
async def test_recover_stale_jobs_respects_limit():
    jobs = [make_job(), make_job(), make_job()]
    repository = FakeJobRepository(jobs)
    service = EmbeddingJobRecoveryService(
        db=FakeDb(),
        job_repository=repository,
        document_repository=SimpleNamespace(),
    )
    service.status_service = FakeStatusService()

    recovered = await service.recover_stale_jobs(stale_minutes=10, limit=2)

    assert recovered == jobs[:2]
    assert repository.find_calls[0]["limit"] == 2
