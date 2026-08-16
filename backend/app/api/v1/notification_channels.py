from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.exceptions import AppException
from app.common.responses import success_response
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.notifications.secret_store import (
    NotificationSecretStore, SecretStoreUnavailableError, get_notification_secret_store,
)
from app.schemas.notification import NotificationChannelResponse, SlackChannelUpdate
from app.services.notification_channel_service import NotificationChannelService

router = APIRouter(prefix="/notification-channels", tags=["Notification Channels"])


def response(setting, configured: bool) -> NotificationChannelResponse:
    if setting is None:
        return NotificationChannelResponse()
    return NotificationChannelResponse(
        enabled=setting.enabled, configured=configured,
        destination_label=setting.destination_label,
        subscribed_event_types=setting.subscribed_event_types,
    )


@router.get("/slack")
async def get_slack_channel(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    service = NotificationChannelService(db, secret_store, settings.app_env)
    setting = await service.get_slack(current_user.id)
    try:
        configured = await service.configured(setting)
    except SecretStoreUnavailableError as exc:
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_STORE_UNAVAILABLE", str(exc))
    return success_response(data=response(setting, configured), message="Slack notification setting fetched successfully.")


@router.put("/slack")
async def put_slack_channel(
    request: SlackChannelUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    service = NotificationChannelService(db, secret_store, settings.app_env)
    try:
        setting = await service.update_slack(current_user.id, request)
        configured = await service.configured(setting)
    except ValueError as exc:
        raise AppException(status.HTTP_422_UNPROCESSABLE_CONTENT, "INVALID_SLACK_SETTING", str(exc))
    except SecretStoreUnavailableError as exc:
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_STORE_UNAVAILABLE", str(exc))
    return success_response(data=response(setting, configured), message="Slack notification setting saved successfully.")


@router.delete("/slack")
async def delete_slack_channel(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
    secret_store: NotificationSecretStore = Depends(get_notification_secret_store),
):
    service = NotificationChannelService(db, secret_store, settings.app_env)
    try:
        await service.delete_slack(current_user.id)
    except SecretStoreUnavailableError as exc:
        raise AppException(status.HTTP_503_SERVICE_UNAVAILABLE, "SECRET_STORE_UNAVAILABLE", str(exc))
    return success_response(data=NotificationChannelResponse(), message="Slack integration removed successfully.")
