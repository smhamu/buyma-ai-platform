from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.notification_channel_setting import NotificationChannelSetting
from app.models.notification_delivery import NotificationDelivery
from app.models.notification_outbox import NotificationOutbox
from app.notifications.secret_store import SecretNotFoundError, SecretStoreUnavailableError
from app.notifications.slack import SlackNotificationAdapter
from app.services.notification_outbox_consumer import DeliveryResult, OutboxDeliveryEvent


class NotificationOutboxExpansionService:
    def __init__(self, db, resolver, *, lease_seconds=300):
        self.db = db; self.resolver = resolver; self.lease_seconds = max(1, lease_seconds)

    async def claim(self, batch_size, now=None):
        now = now or datetime.now(timezone.utc); cutoff = now - timedelta(seconds=self.lease_seconds)
        try:
            await self.db.execute(
                update(NotificationOutbox).where(
                    NotificationOutbox.status == "processing",
                    or_(NotificationOutbox.lease_expires_at <= now, NotificationOutbox.updated_at <= cutoff),
                ).values(status="pending", available_at=now, processing_started_at=None, lease_expires_at=None)
            )
            rows = await self.db.execute(
                select(NotificationOutbox).where(
                    NotificationOutbox.status == "pending", NotificationOutbox.available_at <= now,
                ).order_by(NotificationOutbox.available_at).limit(max(1, batch_size)).with_for_update(skip_locked=True)
            )
            events = list(rows.scalars().all())
            for event in events:
                event.status = "processing"; event.processing_started_at = now
                event.lease_expires_at = now + timedelta(seconds=self.lease_seconds); event.attempt_count += 1
            await self.db.commit()
            return events
        except Exception:
            await self.db.rollback()
            raise

    async def expand_batch(self, batch_size, now=None):
        now = now or datetime.now(timezone.utc); events = await self.claim(batch_size, now)
        expanded = cancelled = retried = 0
        for event in events:
            try:
                channels = await self.resolver.resolve(event.owner_user_id, event.event_type)
                for channel in channels:
                    delivery_id = uuid4()
                    await self.db.execute(
                        pg_insert(NotificationDelivery).values(
                            id=delivery_id, outbox_id=event.id, channel_setting_id=channel.id,
                            user_id=event.owner_user_id, channel_type=channel.channel_type,
                            event_type=event.event_type, resource_id=event.resource_id,
                            status="pending", available_at=now, attempt_count=0,
                            idempotency_key=f"notification-delivery:{delivery_id}",
                        ).on_conflict_do_nothing(index_elements=["outbox_id","channel_setting_id"])
                    )
                event.status = "expanded" if channels else "cancelled"
                event.processed_at = now; event.processing_started_at = None; event.lease_expires_at = None
                await self.db.commit()
                expanded += bool(channels); cancelled += not channels
            except Exception:
                await self.db.rollback()
                current = await self.db.scalar(select(NotificationOutbox).where(NotificationOutbox.id == event.id))
                if current:
                    current.status = "pending"; current.available_at = now + timedelta(seconds=60)
                    current.processing_started_at = None; current.lease_expires_at = None
                    current.last_error = "Notification channel resolution failed."
                    await self.db.commit()
                retried += 1
        return {"claimed": len(events), "expanded": expanded, "cancelled": cancelled, "retried": retried}


class NotificationDeliveryConsumerService:
    def __init__(self, db, secret_store, *, max_attempts=5, base_backoff_seconds=60, max_backoff_seconds=3600, lease_seconds=300, frontend_base_url=None):
        self.db=db; self.secret_store=secret_store; self.max_attempts=max(1,max_attempts)
        self.base_backoff_seconds=max(1,base_backoff_seconds);self.max_backoff_seconds=max(self.base_backoff_seconds,max_backoff_seconds)
        self.lease_seconds=max(1,lease_seconds);self.frontend_base_url=frontend_base_url

    def backoff(self, attempts): return min(self.base_backoff_seconds*(2**max(0,attempts-1)),self.max_backoff_seconds)

    async def claim(self,batch_size,now=None):
        now=now or datetime.now(timezone.utc);cutoff=now-timedelta(seconds=self.lease_seconds)
        try:
            await self.db.execute(update(NotificationDelivery).where(
                NotificationDelivery.status=="processing",
                or_(NotificationDelivery.lease_expires_at<=now,NotificationDelivery.updated_at<=cutoff),
            ).values(status="pending",available_at=now,processing_started_at=None,lease_expires_at=None,last_error="Processing lease expired; delivery was recovered."))
            rows=await self.db.execute(select(NotificationDelivery).where(
                NotificationDelivery.status=="pending",NotificationDelivery.available_at<=now,
            ).order_by(NotificationDelivery.available_at).limit(max(1,batch_size)).with_for_update(skip_locked=True))
            deliveries=list(rows.scalars().all())
            for item in deliveries:
                item.status="processing";item.processing_started_at=now;item.lease_expires_at=now+timedelta(seconds=self.lease_seconds);item.attempt_count+=1
            await self.db.commit();return deliveries
        except Exception:
            await self.db.rollback();raise

    async def _finish(self,item,result,now):
        current=await self.db.scalar(select(NotificationDelivery).where(NotificationDelivery.id==item.id).with_for_update())
        if current is None or current.status!="processing":return "ignored"
        current.processing_started_at=None;current.lease_expires_at=None;current.provider_status_code=result.provider_status_code
        if result.success:
            current.status="delivered";current.delivered_at=now;current.last_error=None;outcome="delivered"
        elif result.retryable and current.attempt_count<self.max_attempts:
            delay=max(self.backoff(current.attempt_count),result.retry_after_seconds or 0)
            current.status="pending";current.available_at=now+timedelta(seconds=delay)
            current.last_error=result.safe_error_code or "delivery_retryable";outcome="retried"
        else:
            current.status="failed";current.last_error=result.safe_error_code or "delivery_failed";outcome="failed"
        await self.db.commit();return outcome

    async def consume_batch(self,batch_size,now=None):
        now=now or datetime.now(timezone.utc);items=await self.claim(batch_size,now);counts={"delivered":0,"retried":0,"failed":0}
        for item in items:
            try:
                setting=await self.db.scalar(select(NotificationChannelSetting).where(
                    NotificationChannelSetting.id==item.channel_setting_id,
                    NotificationChannelSetting.user_id==item.user_id,
                    NotificationChannelSetting.enabled.is_(True),
                ))
                outbox=await self.db.scalar(select(NotificationOutbox).where(
                    NotificationOutbox.id==item.outbox_id,NotificationOutbox.owner_user_id==item.user_id,
                ))
                if (
                    setting is None or outbox is None
                    or setting.user_id != item.user_id or outbox.owner_user_id != item.user_id
                    or item.event_type not in (setting.subscribed_event_types or [])
                ):
                    result=DeliveryResult(False,False,safe_error_code="notification_setting_unavailable")
                else:
                    secret=await self.secret_store.get_secret(setting.secret_reference)
                    if item.channel_type!="slack":
                        result=DeliveryResult(False,False,safe_error_code="unsupported_notification_channel")
                    else:
                        adapter=SlackNotificationAdapter(secret,frontend_base_url=self.frontend_base_url)
                        result=await adapter.deliver(OutboxDeliveryEvent(
                            id=outbox.id,event_type=outbox.event_type,resource_type=outbox.resource_type,
                            resource_id=outbox.resource_id,payload=outbox.payload,idempotency_key=item.idempotency_key,
                        ))
            except SecretNotFoundError:
                result=DeliveryResult(False,False,safe_error_code="notification_secret_missing")
            except SecretStoreUnavailableError:
                result=DeliveryResult(False,True,safe_error_code="notification_secret_store_unavailable")
            except Exception:
                result=DeliveryResult(False,True,safe_error_code="notification_delivery_error")
            outcome=await self._finish(item,result,now)
            if outcome in counts:counts[outcome]+=1
        return {"claimed":len(items),**counts}

    async def retry_failed(self,delivery_id,owner_user_id=None,now=None):
        filters=[NotificationDelivery.id==delivery_id]
        if owner_user_id is not None:filters.append(NotificationDelivery.user_id==owner_user_id)
        item=await self.db.scalar(select(NotificationDelivery).where(*filters).with_for_update())
        if item is None:return None
        if item.status!="failed":raise ValueError("Only failed deliveries can be retried.")
        item.status="pending";item.available_at=now or datetime.now(timezone.utc);item.attempt_count=0
        item.delivered_at=None;item.last_error=None;item.provider_status_code=None
        await self.db.commit();await self.db.refresh(item);return item
