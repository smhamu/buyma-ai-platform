from uuid import uuid4

import pytest

from app.notifications.secret_store import InMemoryNotificationSecretStore, SecretNotFoundError, slack_secret_reference


@pytest.mark.asyncio
async def test_memory_secret_lifecycle_and_safe_uuid_path():
    store=InMemoryNotificationSecretStore();reference=slack_secret_reference(uuid4(),"test")
    assert reference.startswith("/buyma-ai/test/users/") and ".." not in reference
    assert not await store.exists(reference);await store.put_secret(reference,"secret")
    assert await store.exists(reference) and await store.get_secret(reference)=="secret"
    await store.delete_secret(reference);assert not await store.exists(reference)
    with pytest.raises(SecretNotFoundError):await store.get_secret(reference)
