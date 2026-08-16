from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_outbox import NotificationOutbox


@dataclass(frozen=True)
class OutboxDeliveryEvent:
    id: UUID
    event_type: str
    resource_type: str
    resource_id: UUID
    payload: dict
    idempotency_key: str


@dataclass(frozen=True)
class DeliveryResult:
    success: bool
    retryable: bool = False
    error: str | None = None


class NotificationChannelAdapter(Protocol):
    async def deliver(self, event: OutboxDeliveryEvent) -> DeliveryResult: ...


class NoopNotificationAdapter:
    """Test/development adapter. It must never be enabled as production delivery."""

    async def deliver(self, event: OutboxDeliveryEvent) -> DeliveryResult:
        return DeliveryResult(success=True)


@dataclass(frozen=True)
class BatchResult:
    claimed: int = 0
    delivered: int = 0
    retried: int = 0
    failed: int = 0


class NotificationOutboxConsumerService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        max_attempts: int = 5,
        base_backoff_seconds: int = 60,
        max_backoff_seconds: int = 3600,
        lease_seconds: int = 300,
    ):
        self.db = db
        self.max_attempts = max(1, max_attempts)
        self.base_backoff_seconds = max(1, base_backoff_seconds)
        self.max_backoff_seconds = max(self.base_backoff_seconds, max_backoff_seconds)
        self.lease_seconds = max(1, lease_seconds)

    @staticmethod
    def claim_query(batch_size: int, now: datetime):
        return (
            select(NotificationOutbox)
            .where(
                NotificationOutbox.status == "pending",
                NotificationOutbox.available_at <= now,
            )
            .order_by(NotificationOutbox.available_at, NotificationOutbox.created_at)
            .limit(max(1, batch_size))
            .with_for_update(skip_locked=True)
        )

    async def claim(self, batch_size: int, *, now: datetime | None = None) -> list[NotificationOutbox]:
        now = now or datetime.now(timezone.utc)
        try:
            legacy_lease_cutoff = now - timedelta(seconds=self.lease_seconds)
            await self.db.execute(
                update(NotificationOutbox)
                .where(
                    NotificationOutbox.status == "processing",
                    or_(
                        NotificationOutbox.lease_expires_at <= now,
                        (
                            NotificationOutbox.lease_expires_at.is_(None)
                            & (NotificationOutbox.processing_started_at <= legacy_lease_cutoff)
                        ),
                        (
                            NotificationOutbox.lease_expires_at.is_(None)
                            & NotificationOutbox.processing_started_at.is_(None)
                            & (NotificationOutbox.updated_at <= legacy_lease_cutoff)
                        ),
                    ),
                )
                .values(
                    status="pending",
                    available_at=now,
                    processing_started_at=None,
                    lease_expires_at=None,
                    last_error="Processing lease expired; event was recovered.",
                )
            )
            result = await self.db.execute(self.claim_query(batch_size, now))
            events = list(result.scalars().all())
            lease_expires_at = now + timedelta(seconds=self.lease_seconds)
            for event in events:
                event.status = "processing"
                event.processing_started_at = now
                event.lease_expires_at = lease_expires_at
                event.attempt_count += 1
            await self.db.commit()
            return events
        except Exception:
            await self.db.rollback()
            raise

    async def requeue_failed(
        self, event_id: UUID, *, owner_user_id: UUID | None = None, now: datetime | None = None
    ) -> NotificationOutbox | None:
        now = now or datetime.now(timezone.utc)
        filters = [NotificationOutbox.id == event_id]
        if owner_user_id is not None:
            filters.append(NotificationOutbox.owner_user_id == owner_user_id)
        try:
            event = await self.db.scalar(
                select(NotificationOutbox).where(*filters).with_for_update()
            )
            if event is None:
                return None
            if event.status != "failed":
                raise ValueError("Only failed events can be retried.")
            event.status = "pending"
            event.available_at = now
            event.processed_at = None
            event.processing_started_at = None
            event.lease_expires_at = None
            event.attempt_count = 0
            event.last_error = None
            await self.db.commit()
            await self.db.refresh(event)
            return event
        except Exception:
            await self.db.rollback()
            raise

    def backoff_seconds(self, attempt_count: int) -> int:
        exponent = max(0, attempt_count - 1)
        return min(self.base_backoff_seconds * (2**exponent), self.max_backoff_seconds)

    @staticmethod
    def _safe_error(error: str | None) -> str:
        value = error or "Notification delivery failed."
        value = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", value)
        value = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", value)
        return value[:1000]

    async def mark_delivered(self, event_id: UUID, *, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        event = await self.db.scalar(
            select(NotificationOutbox).where(NotificationOutbox.id == event_id).with_for_update()
        )
        if event is None or event.status != "processing":
            return
        event.status = "delivered"
        event.processed_at = now
        event.processing_started_at = None
        event.lease_expires_at = None
        event.last_error = None
        await self.db.commit()

    async def mark_failure(
        self, event_id: UUID, *, error: str | None, retryable: bool, now: datetime | None = None
    ) -> str:
        now = now or datetime.now(timezone.utc)
        event = await self.db.scalar(
            select(NotificationOutbox).where(NotificationOutbox.id == event_id).with_for_update()
        )
        if event is None or event.status != "processing":
            return "ignored"
        event.last_error = self._safe_error(error)
        event.processing_started_at = None
        event.lease_expires_at = None
        if retryable and event.attempt_count < self.max_attempts:
            event.status = "pending"
            event.available_at = now + timedelta(seconds=self.backoff_seconds(event.attempt_count))
            outcome = "retried"
        else:
            event.status = "failed"
            event.processed_at = now
            outcome = "failed"
        await self.db.commit()
        return outcome

    async def dispatch_batch(
        self, adapter: NotificationChannelAdapter, batch_size: int, *, now: datetime | None = None
    ) -> BatchResult:
        events = await self.claim(batch_size, now=now)
        delivered = retried = failed = 0
        for row in events:
            event = OutboxDeliveryEvent(
                id=row.id,
                event_type=row.event_type,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                payload=row.payload,
                idempotency_key=row.dedupe_key or str(row.id),
            )
            try:
                result = await adapter.deliver(event)
            except Exception as exc:  # adapter failures belong to the event, not the Celery task
                result = DeliveryResult(success=False, retryable=True, error=str(exc))
            if result.success:
                await self.mark_delivered(row.id, now=now)
                delivered += 1
                continue
            outcome = await self.mark_failure(
                row.id, error=result.error, retryable=result.retryable, now=now
            )
            retried += outcome == "retried"
            failed += outcome == "failed"
        return BatchResult(len(events), delivered, retried, failed)
