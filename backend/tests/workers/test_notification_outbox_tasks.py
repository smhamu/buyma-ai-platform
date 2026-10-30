import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.workers.notification_outbox_tasks import (
    consume_notification_delivery_batch,
    expand_notification_outbox_batch,
)


class FakeSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None


class FakeEngine:
    def __init__(self):
        self.dispose = AsyncMock()


def configure_worker_batch(monkeypatch, service_name, result=None, error=None):
    from app.workers import notification_outbox_tasks

    sessions = []
    engines = []

    async def create_session():
        session = FakeSession()
        engine = FakeEngine()
        sessions.append(session)
        engines.append(engine)
        return session, engine

    class Service:
        def __init__(self, *_args, **_kwargs):
            pass

        async def expand_batch(self, _batch_size):
            if error:
                raise error
            return result or {"claimed": 1}

        async def consume_batch(self, _batch_size):
            if error:
                raise error
            return result or {"claimed": 1}

    monkeypatch.setattr(notification_outbox_tasks, "create_worker_session", create_session)
    monkeypatch.setattr(notification_outbox_tasks, service_name, Service)
    monkeypatch.setattr(notification_outbox_tasks, "get_notification_secret_store", lambda: object())
    monkeypatch.setattr(notification_outbox_tasks.settings, "notification_outbox_consumer_enabled", True)
    return sessions, engines


@pytest.mark.asyncio
async def test_tasks_are_safe_when_consumer_is_disabled():
    with patch("app.workers.notification_outbox_tasks.settings.notification_outbox_consumer_enabled",False):
        expansion=await expand_notification_outbox_batch();delivery=await consume_notification_delivery_batch()
    assert expansion=={"enabled":False,"kind":"outbox_expansion","claimed":0}
    assert delivery=={"enabled":False,"kind":"delivery","claimed":0}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service_name", "batch", "kind"),
    [
        ("NotificationOutboxExpansionService", expand_notification_outbox_batch, "outbox_expansion"),
        ("NotificationDeliveryConsumerService", consume_notification_delivery_batch, "delivery"),
    ],
)
async def test_batches_use_worker_session_and_dispose_engine(monkeypatch, service_name, batch, kind):
    sessions, engines = configure_worker_batch(monkeypatch, service_name)

    result = await batch()

    assert result == {"enabled": True, "kind": kind, "claimed": 1}
    assert len(sessions) == 1
    engines[0].dispose.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service_name", "batch"),
    [
        ("NotificationOutboxExpansionService", expand_notification_outbox_batch),
        ("NotificationDeliveryConsumerService", consume_notification_delivery_batch),
    ],
)
async def test_batches_dispose_engine_when_processing_fails(monkeypatch, service_name, batch):
    _, engines = configure_worker_batch(
        monkeypatch, service_name, error=RuntimeError("safe test failure")
    )

    with pytest.raises(RuntimeError, match="safe test failure"):
        await batch()

    engines[0].dispose.assert_awaited_once()


def test_batches_can_run_across_fresh_event_loops(monkeypatch):
    from app.workers import notification_outbox_tasks

    _, engines = configure_worker_batch(
        monkeypatch, "NotificationOutboxExpansionService"
    )
    monkeypatch.setattr(
        notification_outbox_tasks, "NotificationDeliveryConsumerService",
        notification_outbox_tasks.NotificationOutboxExpansionService,
    )

    asyncio.run(expand_notification_outbox_batch())
    asyncio.run(consume_notification_delivery_batch())
    asyncio.run(expand_notification_outbox_batch())

    assert len(engines) == 3
    for engine in engines:
        engine.dispose.assert_awaited_once()


def test_production_rejects_memory_secret_store_in_configuration():
    from app.core.config import Settings
    from pydantic import ValidationError
    with pytest.raises(ValidationError,match="must use the SSM"):
        Settings(_env_file=None,app_env="production",database_url="postgresql+asyncpg://u:p@db/x",secret_key="x"*40,notification_secret_store="memory")
