from fastapi import APIRouter, Depends, status

from app.api.deps import require_admin
from app.common.exceptions import AppException
from app.common.responses import success_response
from app.core.config import settings
from app.models.user import User
from app.notifications.secret_store import (
    NotificationSecretStore,
    SecretStoreUnavailableError,
    get_notification_secret_store,
    rakuten_product_search_token_reference,
)
from app.schemas.integration_setting import RakutenTokenSettingResponse, RakutenTokenUpdate

router = APIRouter(prefix="/integration-settings", tags=["Integration Settings"])


def _reference() -> str:
    return rakuten_product_search_token_reference(settings.app_env)


@router.get("/rakuten", response_model=None)
async def get_rakuten_setting(
    _: User = Depends(require_admin),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    try:
        configured = await secret_store.exists(_reference())
    except SecretStoreUnavailableError as exc:
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_STORE_UNAVAILABLE", str(exc))
    return success_response(
        data=RakutenTokenSettingResponse(configured=configured),
        message="Rakuten integration setting fetched successfully.",
    )


@router.put("/rakuten", response_model=None)
async def put_rakuten_setting(
    request: RakutenTokenUpdate,
    _: User = Depends(require_admin),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    try:
        await secret_store.put_secret(_reference(), request.token)
    except SecretStoreUnavailableError as exc:
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_STORE_UNAVAILABLE", str(exc))
    return success_response(
        data=RakutenTokenSettingResponse(configured=True),
        message="Rakuten integration setting saved successfully.",
    )


@router.delete("/rakuten", response_model=None)
async def delete_rakuten_setting(
    _: User = Depends(require_admin),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    try:
        await secret_store.delete_secret(_reference())
    except SecretStoreUnavailableError as exc:
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_STORE_UNAVAILABLE", str(exc))
    return success_response(
        data=RakutenTokenSettingResponse(),
        message="Rakuten integration setting removed successfully.",
    )
