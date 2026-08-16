import asyncio

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.notifications.secret_store import get_notification_secret_store
from app.services.notification_channel_service import NotificationChannelResolver
from app.services.notification_delivery_service import NotificationDeliveryConsumerService, NotificationOutboxExpansionService
from app.workers.celery_app import celery_app


def disabled_result(kind):
    return {"enabled": False, "kind": kind, "claimed": 0}


async def expand_notification_outbox_batch() -> dict:
    if not settings.notification_outbox_consumer_enabled:
        return disabled_result("outbox_expansion")
    secret_store = get_notification_secret_store()
    async with AsyncSessionLocal() as db:
        service = NotificationOutboxExpansionService(
            db, NotificationChannelResolver(db, secret_store),
            lease_seconds=settings.notification_outbox_lease_seconds,
        )
        result = await service.expand_batch(settings.notification_outbox_batch_size)
        return {"enabled": True, "kind": "outbox_expansion", **result}


async def consume_notification_delivery_batch() -> dict:
    if not settings.notification_outbox_consumer_enabled:
        return disabled_result("delivery")
    async with AsyncSessionLocal() as db:
        service = NotificationDeliveryConsumerService(
            db, get_notification_secret_store(),
            max_attempts=settings.notification_outbox_max_attempts,
            base_backoff_seconds=settings.notification_outbox_base_backoff_seconds,
            max_backoff_seconds=settings.notification_outbox_max_backoff_seconds,
            lease_seconds=settings.notification_outbox_lease_seconds,
            frontend_base_url=settings.production_base_url,
        )
        result = await service.consume_batch(settings.notification_outbox_batch_size)
        return {"enabled": True, "kind": "delivery", **result}


@celery_app.task(name="notification_outbox.expand", max_retries=0)
def expand_notification_outbox() -> dict:
    return asyncio.run(expand_notification_outbox_batch())


@celery_app.task(name="notification_delivery.consume", max_retries=0)
def consume_notification_delivery() -> dict:
    return asyncio.run(consume_notification_delivery_batch())


@celery_app.task(name="notification_outbox.consume", max_retries=0)
def consume_notification_outbox() -> dict:
    """Deprecated compatibility entrypoint; new schedules use separate tasks."""
    return {
        "deprecated": True,
        "expansion": asyncio.run(expand_notification_outbox_batch()),
        "delivery": asyncio.run(consume_notification_delivery_batch()),
    }
