from unittest.mock import patch

import pytest

from app.notifications.slack import SlackNotificationAdapter
from app.workers.notification_outbox_tasks import build_notification_adapter, consume_notification_outbox_batch


@pytest.mark.asyncio
async def test_consumer_task_is_safe_when_delivery_is_disabled():
    with patch("app.workers.notification_outbox_tasks.settings.notification_outbox_consumer_enabled", False):
        result = await consume_notification_outbox_batch()
    assert result == {"enabled": False, "claimed": 0, "delivered": 0, "retried": 0, "failed": 0}


@pytest.mark.asyncio
async def test_noop_adapter_is_rejected_in_production():
    with (
        patch("app.workers.notification_outbox_tasks.settings.notification_outbox_consumer_enabled", True),
        patch("app.workers.notification_outbox_tasks.settings.notification_delivery_provider", "noop"),
        patch("app.workers.notification_outbox_tasks.settings.app_env", "production"),
    ):
        with pytest.raises(RuntimeError, match="cannot be enabled in production"):
            await consume_notification_outbox_batch()


@pytest.mark.asyncio
async def test_slack_provider_requires_secret_before_claiming():
    with (
        patch("app.workers.notification_outbox_tasks.settings.notification_outbox_consumer_enabled", True),
        patch("app.workers.notification_outbox_tasks.settings.notification_delivery_provider", "slack"),
        patch("app.workers.notification_outbox_tasks.settings.slack_webhook_url", None),
    ):
        with pytest.raises(RuntimeError, match="SLACK_WEBHOOK_URL"):
            await consume_notification_outbox_batch()


def test_configured_slack_provider_selects_slack_adapter_without_network():
    with (
        patch("app.workers.notification_outbox_tasks.settings.notification_delivery_provider", "slack"),
        patch(
            "app.workers.notification_outbox_tasks.settings.slack_webhook_url",
            "https://hooks.slack.com/services/a/b/c",
        ),
    ):
        assert isinstance(build_notification_adapter(), SlackNotificationAdapter)
