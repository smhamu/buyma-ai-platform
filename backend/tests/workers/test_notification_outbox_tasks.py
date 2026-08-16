from unittest.mock import patch

import pytest

from app.workers.notification_outbox_tasks import consume_notification_outbox_batch


@pytest.mark.asyncio
async def test_consumer_task_is_safe_when_delivery_is_disabled():
    with patch("app.workers.notification_outbox_tasks.settings.notification_outbox_consumer_enabled", False):
        result = await consume_notification_outbox_batch()
    assert result == {"enabled": False, "claimed": 0, "delivered": 0, "retried": 0, "failed": 0}


@pytest.mark.asyncio
async def test_noop_adapter_is_rejected_in_production():
    with (
        patch("app.workers.notification_outbox_tasks.settings.notification_outbox_consumer_enabled", True),
        patch("app.workers.notification_outbox_tasks.settings.notification_outbox_adapter", "noop"),
        patch("app.workers.notification_outbox_tasks.settings.app_env", "production"),
    ):
        with pytest.raises(RuntimeError, match="cannot be enabled in production"):
            await consume_notification_outbox_batch()
