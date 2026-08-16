import asyncio

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.notification_outbox_consumer import (
    NoopNotificationAdapter,
    NotificationOutboxConsumerService,
)
from app.workers.celery_app import celery_app


async def consume_notification_outbox_batch() -> dict:
    if not settings.notification_outbox_consumer_enabled:
        return {"enabled": False, "claimed": 0, "delivered": 0, "retried": 0, "failed": 0}
    if settings.notification_outbox_adapter != "noop":
        raise RuntimeError("No notification channel adapter is configured.")
    if settings.app_env == "production":
        raise RuntimeError("The noop notification adapter cannot be enabled in production.")
    async with AsyncSessionLocal() as db:
        service = NotificationOutboxConsumerService(
            db,
            max_attempts=settings.notification_outbox_max_attempts,
            base_backoff_seconds=settings.notification_outbox_base_backoff_seconds,
            max_backoff_seconds=settings.notification_outbox_max_backoff_seconds,
            lease_seconds=settings.notification_outbox_lease_seconds,
        )
        result = await service.dispatch_batch(
            NoopNotificationAdapter(), settings.notification_outbox_batch_size
        )
        return {"enabled": True, **result.__dict__}


@celery_app.task(name="notification_outbox.consume", max_retries=0)
def consume_notification_outbox() -> dict:
    return asyncio.run(consume_notification_outbox_batch())
