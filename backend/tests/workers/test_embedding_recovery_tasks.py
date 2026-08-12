from uuid import UUID, uuid4

from app.workers import embedding_recovery_tasks


def test_recover_stale_jobs_task_enqueues_recovered_jobs(monkeypatch):
    job_ids = [uuid4(), uuid4()]

    async def fake_recover_stale_jobs():
        return [str(job_id) for job_id in job_ids]

    class FakeQueueService:
        def __init__(self):
            self.enqueued = []

        def enqueue(self, job_id):
            assert isinstance(job_id, UUID)
            self.enqueued.append(job_id)
            return f"task-{job_id}"

    queue_service = FakeQueueService()
    monkeypatch.setattr(
        embedding_recovery_tasks,
        "_recover_stale_jobs",
        fake_recover_stale_jobs,
    )
    monkeypatch.setattr(
        embedding_recovery_tasks,
        "EmbeddingQueueService",
        lambda: queue_service,
    )

    result = embedding_recovery_tasks.recover_stale_jobs_task.run()

    assert queue_service.enqueued == job_ids
    assert result["recovered_count"] == 2
    assert result["job_ids"] == [str(job_id) for job_id in job_ids]
    assert result["task_ids"] == [f"task-{job_id}" for job_id in job_ids]


def test_recover_stale_jobs_task_does_not_enqueue_when_no_jobs(monkeypatch):
    class FakeQueueService:
        def enqueue(self, job_id):
            raise AssertionError("enqueue must not be called")

    async def fake_recover_stale_jobs():
        return []

    monkeypatch.setattr(
        embedding_recovery_tasks,
        "_recover_stale_jobs",
        fake_recover_stale_jobs,
    )
    monkeypatch.setattr(
        embedding_recovery_tasks,
        "EmbeddingQueueService",
        FakeQueueService,
    )

    result = embedding_recovery_tasks.recover_stale_jobs_task.run()

    assert result == {
        "recovered_count": 0,
        "job_ids": [],
        "task_ids": [],
    }
