from unittest.mock import patch

import pytest

from app.workers.notification_outbox_tasks import (
    consume_notification_delivery_batch,
    expand_notification_outbox_batch,
)


@pytest.mark.asyncio
async def test_tasks_are_safe_when_consumer_is_disabled():
    with patch("app.workers.notification_outbox_tasks.settings.notification_outbox_consumer_enabled",False):
        expansion=await expand_notification_outbox_batch();delivery=await consume_notification_delivery_batch()
    assert expansion=={"enabled":False,"kind":"outbox_expansion","claimed":0}
    assert delivery=={"enabled":False,"kind":"delivery","claimed":0}


def test_production_rejects_memory_secret_store_in_configuration():
    from app.core.config import Settings
    from pydantic import ValidationError
    with pytest.raises(ValidationError,match="in-memory"):
        Settings(_env_file=None,app_env="production",database_url="postgresql+asyncpg://u:p@db/x",secret_key="x"*40,notification_secret_store="memory")
