from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.services.notification_outbox_consumer import (
    DeliveryResult,
    NotificationOutboxConsumerService,
)


def event(status="processing", attempts=1):
    return SimpleNamespace(
        id=uuid4(), event_type="supplier_policy_review_changed", resource_type="supplier",
        resource_id=uuid4(), payload={"safe": True}, dedupe_key=f"event:{uuid4()}",
        status=status, attempt_count=attempts, available_at=datetime.now(timezone.utc),
        processed_at=None, processing_started_at=None, lease_expires_at=None, last_error=None,
    )


def service(db=None, **kwargs):
    db = db or SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock(), scalar=AsyncMock())
    return NotificationOutboxConsumerService(db, **kwargs), db


def test_claim_query_uses_pending_available_and_skip_locked():
    query = NotificationOutboxConsumerService.claim_query(10, datetime.now(timezone.utc))
    sql = str(query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "status = 'pending'" in sql
    assert "available_at <=" in sql
    assert "LIMIT 10" in sql
    assert "FOR UPDATE SKIP LOCKED" in sql


@pytest.mark.asyncio
async def test_batch_claim_marks_processing_and_prevents_pending_reclaim_shape():
    first, second = event("pending", 0), event("pending", 2)
    scalars = SimpleNamespace(all=lambda: [first, second])
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[object(), SimpleNamespace(scalars=lambda: scalars)]),
        commit=AsyncMock(), rollback=AsyncMock(),
    )
    consumer = NotificationOutboxConsumerService(db, lease_seconds=30)
    claimed = await consumer.claim(2)
    assert claimed == [first, second]
    assert [item.status for item in claimed] == ["processing", "processing"]
    assert [item.attempt_count for item in claimed] == [1, 3]
    assert all(item.lease_expires_at > item.processing_started_at for item in claimed)
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_claim_transaction_rolls_back_on_commit_failure():
    scalars = SimpleNamespace(all=lambda: [])
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[object(), SimpleNamespace(scalars=lambda: scalars)]),
        commit=AsyncMock(side_effect=RuntimeError("commit failed")), rollback=AsyncMock(),
    )
    with pytest.raises(RuntimeError):
        await NotificationOutboxConsumerService(db).claim(1)
    db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_claim_recovers_stuck_processing_before_selecting_batch():
    scalars = SimpleNamespace(all=lambda: [])
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[object(), SimpleNamespace(scalars=lambda: scalars)]),
        commit=AsyncMock(), rollback=AsyncMock(),
    )
    await NotificationOutboxConsumerService(db, lease_seconds=30).claim(1)
    recovery = db.execute.await_args_list[0].args[0]
    sql = str(recovery.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "status='processing'" in sql.replace(" ", "")
    assert "lease_expires_at" in sql and "processing_started_at" in sql


@pytest.mark.asyncio
async def test_manual_retry_resets_failed_event_and_is_owner_scoped():
    row = event("failed", 5); row.processed_at = datetime.now(timezone.utc); row.last_error = "failed"
    consumer, db = service(); db.scalar.return_value = row; db.refresh = AsyncMock()
    retried = await consumer.requeue_failed(row.id, owner_user_id=uuid4())
    assert retried is row and row.status == "pending" and row.attempt_count == 0
    assert row.processed_at is None and row.last_error is None
    query = db.scalar.await_args.args[0]
    sql = str(query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "owner_user_id" in sql and "FOR UPDATE" in sql


def test_exponential_backoff_is_capped():
    consumer, _ = service(base_backoff_seconds=10, max_backoff_seconds=35)
    assert [consumer.backoff_seconds(n) for n in (1, 2, 3, 4)] == [10, 20, 35, 35]


@pytest.mark.asyncio
async def test_success_marks_delivered_and_clears_lease():
    row = event()
    consumer, db = service(); db.scalar.return_value = row
    await consumer.mark_delivered(row.id)
    assert row.status == "delivered" and row.processed_at is not None
    assert row.processing_started_at is None and row.lease_expires_at is None


@pytest.mark.asyncio
async def test_retry_backoff_then_max_attempts_dead_letters_as_failed():
    now = datetime.now(timezone.utc)
    row = event(attempts=2)
    consumer, db = service(max_attempts=3, base_backoff_seconds=10); db.scalar.return_value = row
    assert await consumer.mark_failure(row.id, error="temporary", retryable=True, now=now) == "retried"
    assert row.status == "pending" and row.available_at == now + timedelta(seconds=20)
    row.status = "processing"; row.attempt_count = 3
    assert await consumer.mark_failure(row.id, error="permanent", retryable=True, now=now) == "failed"
    assert row.status == "failed" and row.processed_at == now


@pytest.mark.asyncio
async def test_retry_after_is_a_minimum_delay():
    now = datetime.now(timezone.utc); row = event(attempts=1)
    consumer, db = service(base_backoff_seconds=10); db.scalar.return_value = row
    await consumer.mark_failure(
        row.id, error="rate limited", retryable=True, retry_after_seconds=45, now=now
    )
    assert row.available_at == now + timedelta(seconds=45)


@pytest.mark.asyncio
async def test_dispatch_isolates_failure_and_passes_idempotency_key():
    bad, good = event(), event()
    consumer, _ = service()
    consumer.claim = AsyncMock(return_value=[bad, good])
    consumer.mark_failure = AsyncMock(return_value="retried")
    consumer.mark_delivered = AsyncMock()
    seen = []

    class Adapter:
        async def deliver(self, item):
            seen.append(item.idempotency_key)
            if item.id == bad.id:
                raise RuntimeError("temporary")
            return DeliveryResult(success=True)

    result = await consumer.dispatch_batch(Adapter(), 2)
    assert result.claimed == 2 and result.delivered == 1 and result.retried == 1
    assert seen == [bad.dedupe_key, good.dedupe_key]
    consumer.mark_delivered.assert_awaited_once_with(good.id, now=None)


def test_errors_are_redacted_before_persistence():
    value = NotificationOutboxConsumerService._safe_error("Bearer secret-token sk-123456789")
    assert "secret-token" not in value and "sk-123456789" not in value
