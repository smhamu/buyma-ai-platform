from __future__ import annotations

import asyncio
from typing import Protocol
from uuid import UUID

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import settings


class SecretNotFoundError(Exception):
    pass


class SecretStoreUnavailableError(Exception):
    pass


class NotificationSecretStore(Protocol):
    async def put_secret(self, reference: str, value: str) -> None: ...
    async def get_secret(self, reference: str) -> str: ...
    async def delete_secret(self, reference: str) -> None: ...
    async def exists(self, reference: str) -> bool: ...


def slack_secret_reference(user_id: UUID, app_env: str) -> str:
    return f"/buyma-ai/{app_env}/users/{user_id}/notifications/slack/webhook"


def rakuten_product_search_token_reference(app_env: str) -> str:
    return f"/buyma-ai/{app_env}/integrations/rakuten/product-search-token"


class InMemoryNotificationSecretStore:
    def __init__(self):
        if settings.app_env == "production":
            raise RuntimeError("In-memory notification secrets are prohibited in production.")
        self._values: dict[str, str] = {}

    async def put_secret(self, reference: str, value: str) -> None:
        self._values[reference] = value

    async def get_secret(self, reference: str) -> str:
        try:
            return self._values[reference]
        except KeyError as exc:
            raise SecretNotFoundError("Notification secret is not configured.") from exc

    async def delete_secret(self, reference: str) -> None:
        self._values.pop(reference, None)

    async def exists(self, reference: str) -> bool:
        return reference in self._values


class RedisNotificationSecretStore:
    """Development-only shared secret storage backed by the existing Redis service."""

    _KEY_PREFIX = "notification-secret:"

    def __init__(self, client=None):
        if settings.app_env == "production":
            raise RuntimeError("Redis notification secrets are prohibited in production.")
        self._client = client or redis.from_url(
            settings.celery_broker_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

    @classmethod
    def _key(cls, reference: str) -> str:
        return f"{cls._KEY_PREFIX}{reference}"

    async def put_secret(self, reference: str, value: str) -> None:
        try:
            await self._client.set(self._key(reference), value)
        except RedisError as exc:
            raise SecretStoreUnavailableError("Notification secret store write failed.") from exc

    async def get_secret(self, reference: str) -> str:
        try:
            value = await self._client.get(self._key(reference))
        except RedisError as exc:
            raise SecretStoreUnavailableError("Notification secret store read failed.") from exc
        if value is None:
            raise SecretNotFoundError("Notification secret is not configured.")
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    async def delete_secret(self, reference: str) -> None:
        try:
            await self._client.delete(self._key(reference))
        except RedisError as exc:
            raise SecretStoreUnavailableError("Notification secret store delete failed.") from exc

    async def exists(self, reference: str) -> bool:
        try:
            return bool(await self._client.exists(self._key(reference)))
        except RedisError as exc:
            raise SecretStoreUnavailableError("Notification secret store read failed.") from exc


class SsmNotificationSecretStore:
    def __init__(self, client=None):
        if client is None:
            import boto3
            client = boto3.client("ssm", region_name=settings.aws_region)
        self._client = client

    async def put_secret(self, reference: str, value: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.put_parameter, Name=reference, Value=value,
                Type="SecureString", Overwrite=True,
            )
        except Exception as exc:
            raise SecretStoreUnavailableError("Notification secret store write failed.") from exc

    async def get_secret(self, reference: str) -> str:
        try:
            result = await asyncio.to_thread(
                self._client.get_parameter, Name=reference, WithDecryption=True
            )
            return result["Parameter"]["Value"]
        except self._client.exceptions.ParameterNotFound as exc:
            raise SecretNotFoundError("Notification secret is not configured.") from exc
        except Exception as exc:
            raise SecretStoreUnavailableError("Notification secret store read failed.") from exc

    async def delete_secret(self, reference: str) -> None:
        try:
            await asyncio.to_thread(self._client.delete_parameter, Name=reference)
        except self._client.exceptions.ParameterNotFound:
            return
        except Exception as exc:
            raise SecretStoreUnavailableError("Notification secret store delete failed.") from exc

    async def exists(self, reference: str) -> bool:
        try:
            await self.get_secret(reference)
            return True
        except SecretNotFoundError:
            return False


_memory_store: InMemoryNotificationSecretStore | None = None
_redis_store: RedisNotificationSecretStore | None = None
_ssm_store: SsmNotificationSecretStore | None = None


def get_notification_secret_store() -> NotificationSecretStore:
    global _memory_store, _redis_store, _ssm_store
    if settings.notification_secret_store == "memory":
        if _memory_store is None:
            _memory_store = InMemoryNotificationSecretStore()
        return _memory_store
    if settings.notification_secret_store == "redis":
        if settings.app_env == "production":
            raise RuntimeError("Redis notification secrets are prohibited in production.")
        if _redis_store is None:
            _redis_store = RedisNotificationSecretStore()
        return _redis_store
    if settings.notification_secret_store == "ssm":
        if _ssm_store is None:
            _ssm_store = SsmNotificationSecretStore()
        return _ssm_store
    raise RuntimeError("Unsupported notification secret store.")
