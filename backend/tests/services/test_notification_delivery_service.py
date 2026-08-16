from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.notification_delivery_service import NotificationDeliveryConsumerService, NotificationOutboxExpansionService
from app.services.notification_outbox_consumer import DeliveryResult


def outbox(user_id):
    now=datetime.now(timezone.utc)
    return SimpleNamespace(id=uuid4(),owner_user_id=user_id,event_type="supplier_policy_review_changed",resource_type="supplier",resource_id=uuid4(),payload={"supplier_name":"Shop"},status="pending",available_at=now,created_at=now,updated_at=now,attempt_count=0,processing_started_at=None,lease_expires_at=None,processed_at=None,last_error=None)


def delivery(user_id,setting_id,outbox_id,status="pending",attempts=0):
    now=datetime.now(timezone.utc)
    return SimpleNamespace(id=uuid4(),user_id=user_id,channel_setting_id=setting_id,outbox_id=outbox_id,channel_type="slack",event_type="supplier_policy_review_changed",resource_id=uuid4(),status=status,available_at=now,updated_at=now,attempt_count=attempts,processing_started_at=None,lease_expires_at=None,delivered_at=None,last_error=None,provider_status_code=None,idempotency_key=f"delivery:{uuid4()}")


@pytest.mark.asyncio
@pytest.mark.parametrize(("channels","expected"),[([],"cancelled"),([1],"expanded")])
async def test_outbox_expands_once_per_resolved_channel_or_cancels(channels,expected):
    user_id=uuid4();event=outbox(user_id);setting=SimpleNamespace(id=uuid4(),channel_type="slack")
    scalar_result=SimpleNamespace(scalars=lambda:SimpleNamespace(all=lambda:[event]))
    db=SimpleNamespace(execute=AsyncMock(side_effect=[object(),scalar_result,object()]),commit=AsyncMock(),rollback=AsyncMock(),scalar=AsyncMock())
    resolver=SimpleNamespace(resolve=AsyncMock(return_value=[setting] if channels else []))
    result=await NotificationOutboxExpansionService(db,resolver).expand_batch(10)
    assert event.status==expected
    assert result["expanded"]==bool(channels) and result["cancelled"]== (not channels)
    assert db.execute.await_count==2+len(channels)


@pytest.mark.asyncio
async def test_delivery_uses_only_owner_setting_secret_and_marks_success():
    user_a,user_b=uuid4(),uuid4();setting_id=uuid4();box=outbox(user_a);item=delivery(user_a,setting_id,box.id)
    setting=SimpleNamespace(id=setting_id,user_id=user_a,enabled=True,channel_type="slack",subscribed_event_types=[item.event_type],secret_reference="/users/a/slack")
    class Store:
        def __init__(self):self.references=[]
        async def get_secret(self,reference):self.references.append(reference);return "https://hooks.slack.com/services/a/b/c"
    store=Store();scalar_values=[setting,box,item]
    db=SimpleNamespace(scalar=AsyncMock(side_effect=scalar_values),commit=AsyncMock(),execute=AsyncMock())
    item.status="processing";service=NotificationDeliveryConsumerService(db,store);service.claim=AsyncMock(return_value=[item])
    adapter=SimpleNamespace(deliver=AsyncMock(return_value=DeliveryResult(True,provider_status_code=200)))
    with patch("app.services.notification_delivery_service.SlackNotificationAdapter",return_value=adapter):result=await service.consume_batch(1)
    assert result["delivered"]==1 and item.status=="delivered"
    assert store.references==["/users/a/slack"] and "/users/b/slack" not in store.references


@pytest.mark.asyncio
@pytest.mark.parametrize(("result","status"),[(DeliveryResult(False,True,safe_error_code="slack_http_429"),"pending"),(DeliveryResult(False,False,safe_error_code="slack_http_400"),"failed")])
async def test_delivery_retryable_and_permanent_results(result,status):
    user=uuid4();setting_id=uuid4();box=outbox(user);item=delivery(user,setting_id,box.id,attempts=1)
    setting=SimpleNamespace(id=setting_id,user_id=user,enabled=True,channel_type="slack",subscribed_event_types=[item.event_type],secret_reference="ref")
    db=SimpleNamespace(scalar=AsyncMock(side_effect=[setting,box,item]),commit=AsyncMock(),execute=AsyncMock());store=SimpleNamespace(get_secret=AsyncMock(return_value="https://hooks.slack.com/services/a/b/c"))
    item.status="processing";service=NotificationDeliveryConsumerService(db,store,max_attempts=3);service.claim=AsyncMock(return_value=[item]);adapter=SimpleNamespace(deliver=AsyncMock(return_value=result))
    with patch("app.services.notification_delivery_service.SlackNotificationAdapter",return_value=adapter):await service.consume_batch(1)
    assert item.status==status


@pytest.mark.asyncio
async def test_max_attempts_fails_and_manual_retry_is_owner_scoped():
    user=uuid4();item=delivery(user,uuid4(),uuid4(),status="processing",attempts=3)
    db=SimpleNamespace(scalar=AsyncMock(return_value=item),commit=AsyncMock(),refresh=AsyncMock())
    service=NotificationDeliveryConsumerService(db,SimpleNamespace(),max_attempts=3)
    await service._finish(item,DeliveryResult(False,True,safe_error_code="temporary"),datetime.now(timezone.utc));assert item.status=="failed"
    retried=await service.retry_failed(item.id,owner_user_id=user);assert retried.status=="pending" and retried.attempt_count==0
    sql=str(db.scalar.await_args.args[0].compile(compile_kwargs={"literal_binds":True}));assert "user_id" in sql
