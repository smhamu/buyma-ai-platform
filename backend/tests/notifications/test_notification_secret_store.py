import logging
from uuid import uuid4

import pytest
from redis.exceptions import ConnectionError

from app.notifications.secret_store import (
    InMemoryNotificationSecretStore,
    RedisNotificationSecretStore,
    SecretNotFoundError,
    SecretStoreUnavailableError,
    slack_secret_reference,
)


class SharedFakeRedis:
    def __init__(self, values=None):
        self.values = values if values is not None else {}

    async def set(self, key, value):
        self.values[key] = value

    async def get(self, key):
        return self.values.get(key)

    async def delete(self, key):
        self.values.pop(key, None)

    async def exists(self, key):
        return int(key in self.values)


class UnavailableRedis(SharedFakeRedis):
    async def set(self, key, value):
        raise ConnectionError("redis unavailable")


@pytest.mark.asyncio
async def test_memory_secret_lifecycle_and_safe_uuid_path():
    store=InMemoryNotificationSecretStore();reference=slack_secret_reference(uuid4(),"test")
    assert reference.startswith("/buyma-ai/test/users/") and ".." not in reference
    assert not await store.exists(reference);await store.put_secret(reference,"secret")
    assert await store.exists(reference) and await store.get_secret(reference)=="secret"
    await store.delete_secret(reference);assert not await store.exists(reference)
    with pytest.raises(SecretNotFoundError):await store.get_secret(reference)


@pytest.mark.asyncio
async def test_redis_secret_lifecycle_and_shared_instances():
    values = {}
    backend_store = RedisNotificationSecretStore(SharedFakeRedis(values))
    worker_store = RedisNotificationSecretStore(SharedFakeRedis(values))
    reference = slack_secret_reference(uuid4(), "development")

    assert not await worker_store.exists(reference)
    with pytest.raises(SecretNotFoundError):
        await worker_store.get_secret(reference)

    await backend_store.put_secret(reference, "private-webhook")

    assert await worker_store.exists(reference)
    assert await worker_store.get_secret(reference) == "private-webhook"
    assert list(values) == [f"notification-secret:{reference}"]

    await worker_store.delete_secret(reference)
    assert not await backend_store.exists(reference)


@pytest.mark.asyncio
async def test_redis_failure_does_not_expose_secret_in_logs(caplog):
    secret = "never-log-this-webhook"
    store = RedisNotificationSecretStore(UnavailableRedis())

    with caplog.at_level(logging.DEBUG), pytest.raises(SecretStoreUnavailableError):
        await store.put_secret(slack_secret_reference(uuid4(), "development"), secret)

    assert secret not in caplog.text
