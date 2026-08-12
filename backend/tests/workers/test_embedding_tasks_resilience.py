from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import (
    AIProviderAuthException,
    AIProviderRateLimitException,
    AIProviderTimeoutException,
    AIProviderUnavailableException,
)
from app.workers import embedding_tasks


def test_is_retryable_exception_only_matches_temporary_provider_errors():
    assert embedding_tasks.is_retryable_exception(AIProviderTimeoutException())
    assert embedding_tasks.is_retryable_exception(AIProviderRateLimitException())
    assert embedding_tasks.is_retryable_exception(AIProviderUnavailableException())
    assert not embedding_tasks.is_retryable_exception(AIProviderAuthException())


class FakeTask:
    max_retries = 3

    def __init__(self, retries=0):
        self.request = SimpleNamespace(retries=retries)
        self.retry_calls = []

    def retry(self, exc, countdown):
        self.retry_calls.append({"exc": exc, "countdown": countdown})
        raise RuntimeError("celery retry scheduled")


def test_retryable_exception_marks_job_pending_and_schedules_retry(monkeypatch):
    job_id = str(uuid4())
    timeout = AIProviderTimeoutException()
    calls = []

    def fake_run(coro):
        name = coro.cr_code.co_name
        locals_ = dict(coro.cr_frame.f_locals)
        coro.close()
        calls.append(name)
        if name == "fake_run_embedding_job":
            raise timeout
        if name == "fake_mark_job_for_retry":
            assert locals_["kwargs"]["job_id"] == job_id
            assert locals_["kwargs"]["retry_count"] == 1
            assert "AI provider request timed out." in locals_["kwargs"]["error_message"]

    async def fake_run_embedding_job(actual_job_id):
        assert actual_job_id == job_id

    async def fake_mark_job_for_retry(**kwargs):
        assert kwargs["job_id"] == job_id
        assert kwargs["retry_count"] == 1
        assert "AI provider request timed out." in kwargs["error_message"]

    async def fake_mark_job_failed(**kwargs):
        raise AssertionError("failed marker must not run before retry exhaustion")

    monkeypatch.setattr(embedding_tasks.asyncio, "run", fake_run)
    monkeypatch.setattr(embedding_tasks, "_run_embedding_job", fake_run_embedding_job)
    monkeypatch.setattr(embedding_tasks, "_mark_job_for_retry", fake_mark_job_for_retry)
    monkeypatch.setattr(embedding_tasks, "_mark_job_failed", fake_mark_job_failed)
    task = FakeTask(retries=0)

    with pytest.raises(RuntimeError, match="celery retry scheduled"):
        embedding_tasks._run_embedding_job_task(task, job_id)

    assert task.retry_calls[0]["countdown"] == 10


def test_retry_exhaustion_marks_job_failed(monkeypatch):
    job_id = str(uuid4())
    timeout = AIProviderTimeoutException()
    failed_calls = []

    def fake_run(coro):
        name = coro.cr_code.co_name
        locals_ = dict(coro.cr_frame.f_locals)
        coro.close()
        if name == "fake_run_embedding_job":
            raise timeout
        if name == "fake_mark_job_failed":
            failed_calls.append(locals_["kwargs"])

    async def fake_run_embedding_job(actual_job_id):
        assert actual_job_id == job_id

    async def fake_mark_job_failed(**kwargs):
        failed_calls.append(kwargs)

    monkeypatch.setattr(embedding_tasks.asyncio, "run", fake_run)
    monkeypatch.setattr(embedding_tasks, "_run_embedding_job", fake_run_embedding_job)
    monkeypatch.setattr(embedding_tasks, "_mark_job_failed", fake_mark_job_failed)
    task = FakeTask(retries=3)

    with pytest.raises(AIProviderTimeoutException):
        embedding_tasks._run_embedding_job_task(task, job_id)

    assert failed_calls[0]["job_id"] == job_id
    assert "Retry limit exceeded:" in failed_calls[0]["error_message"]


def test_non_retryable_exception_marks_job_failed(monkeypatch):
    job_id = str(uuid4())
    auth_error = AIProviderAuthException()
    failed_calls = []

    def fake_run(coro):
        name = coro.cr_code.co_name
        locals_ = dict(coro.cr_frame.f_locals)
        coro.close()
        if name == "fake_run_embedding_job":
            raise auth_error
        if name == "fake_mark_job_failed":
            failed_calls.append(locals_["kwargs"])

    async def fake_run_embedding_job(actual_job_id):
        assert actual_job_id == job_id

    async def fake_mark_job_failed(**kwargs):
        failed_calls.append(kwargs)

    monkeypatch.setattr(embedding_tasks.asyncio, "run", fake_run)
    monkeypatch.setattr(embedding_tasks, "_run_embedding_job", fake_run_embedding_job)
    monkeypatch.setattr(embedding_tasks, "_mark_job_failed", fake_mark_job_failed)
    task = FakeTask(retries=0)

    with pytest.raises(AIProviderAuthException):
        embedding_tasks._run_embedding_job_task(task, job_id)

    assert task.retry_calls == []
    assert failed_calls[0]["job_id"] == job_id
