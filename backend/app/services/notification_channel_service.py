from __future__ import annotations

from sqlalchemy import select, update

from app.models.notification_channel_setting import NotificationChannelSetting
from app.models.notification_delivery import NotificationDelivery
from app.notifications.secret_store import NotificationSecretStore, SecretNotFoundError, slack_secret_reference
from app.notifications.slack import validate_slack_webhook_url

SUPPORTED_EVENT = "supplier_policy_review_changed"


class NotificationChannelService:
    def __init__(self, db, secret_store: NotificationSecretStore, app_env: str):
        self.db = db
        self.secret_store = secret_store
        self.app_env = app_env

    async def get_slack(self, user_id):
        return await self.db.scalar(
            select(NotificationChannelSetting).where(
                NotificationChannelSetting.user_id == user_id,
                NotificationChannelSetting.channel_type == "slack",
            )
        )

    async def configured(self, setting) -> bool:
        return bool(setting and await self.secret_store.exists(setting.secret_reference))

    async def update_slack(self, user_id, request):
        setting = await self.get_slack(user_id)
        reference = setting.secret_reference if setting else slack_secret_reference(user_id, self.app_env)
        old_secret = None
        had_old_secret = False
        try:
            old_secret = await self.secret_store.get_secret(reference)
            had_old_secret = True
        except SecretNotFoundError:
            pass
        if request.webhook_url:
            validate_slack_webhook_url(request.webhook_url)
            await self.secret_store.put_secret(reference, request.webhook_url)
        elif request.enabled and not had_old_secret:
            raise ValueError("A Slack webhook is required before enabling notifications.")
        try:
            if setting is None:
                setting = NotificationChannelSetting(
                    user_id=user_id, channel_type="slack", secret_reference=reference,
                )
                self.db.add(setting)
            setting.enabled = request.enabled
            setting.destination_label = request.destination_label.strip()
            setting.subscribed_event_types = list(request.subscribed_event_types)
            await self.db.commit()
            await self.db.refresh(setting)
            return setting
        except Exception:
            await self.db.rollback()
            if request.webhook_url:
                if had_old_secret and old_secret is not None:
                    await self.secret_store.put_secret(reference, old_secret)
                else:
                    await self.secret_store.delete_secret(reference)
            raise

    async def delete_slack(self, user_id) -> bool:
        setting = await self.get_slack(user_id)
        if setting is None:
            return False
        setting.enabled = False
        await self.db.execute(
            update(NotificationDelivery).where(
                NotificationDelivery.channel_setting_id == setting.id,
                NotificationDelivery.status.in_(["pending", "processing"]),
            ).values(status="cancelled", processing_started_at=None, lease_expires_at=None)
        )
        await self.db.commit()
        await self.secret_store.delete_secret(setting.secret_reference)
        await self.db.delete(setting)
        await self.db.commit()
        return True


class NotificationChannelResolver:
    def __init__(self, db, secret_store: NotificationSecretStore):
        self.db = db
        self.secret_store = secret_store

    async def resolve(self, user_id, event_type):
        rows = await self.db.execute(
            select(NotificationChannelSetting).where(
                NotificationChannelSetting.user_id == user_id,
                NotificationChannelSetting.enabled.is_(True),
            )
        )
        resolved = []
        for setting in rows.scalars().all():
            if event_type not in setting.subscribed_event_types:
                continue
            if await self.secret_store.exists(setting.secret_reference):
                resolved.append(setting)
        return resolved
