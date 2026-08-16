from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.notifications.secret_store import InMemoryNotificationSecretStore, SecretNotFoundError, slack_secret_reference
from app.schemas.notification import NotificationChannelResponse, SlackChannelUpdate
from app.services.notification_channel_service import NotificationChannelResolver, NotificationChannelService


class Db:
    def __init__(self,setting=None):
        self.setting=setting;self.added=[];self.commit=AsyncMock();self.rollback=AsyncMock();self.refresh=AsyncMock();self.delete=AsyncMock();self.execute=AsyncMock()
    async def scalar(self,_):return self.setting
    def add(self,item):self.setting=item;self.added.append(item)


@pytest.mark.asyncio
async def test_create_stores_only_reference_and_response_has_no_secret():
    user_id=uuid4();db=Db();store=InMemoryNotificationSecretStore();service=NotificationChannelService(db,store,"test")
    request=SlackChannelUpdate(enabled=True,webhook_url="https://hooks.slack.com/services/a/b/c",destination_label="Ops",subscribed_event_types=["supplier_policy_review_changed"])
    setting=await service.update_slack(user_id,request)
    assert setting.secret_reference==slack_secret_reference(user_id,"test")
    assert "hooks.slack.com" not in setting.secret_reference
    assert await store.get_secret(setting.secret_reference)==request.webhook_url
    response=NotificationChannelResponse(enabled=setting.enabled,configured=True,destination_label=setting.destination_label,subscribed_event_types=setting.subscribed_event_types)
    assert "webhook" not in response.model_dump_json().lower()


@pytest.mark.asyncio
async def test_update_metadata_without_webhook_preserves_secret_and_disable():
    user_id=uuid4();reference=slack_secret_reference(user_id,"test")
    setting=SimpleNamespace(id=uuid4(),user_id=user_id,channel_type="slack",enabled=True,destination_label="Old",subscribed_event_types=["supplier_policy_review_changed"],secret_reference=reference)
    db=Db(setting);store=InMemoryNotificationSecretStore();await store.put_secret(reference,"https://hooks.slack.com/services/a/b/old")
    result=await NotificationChannelService(db,store,"test").update_slack(user_id,SlackChannelUpdate(enabled=False,destination_label="New",subscribed_event_types=[]))
    assert not result.enabled and result.destination_label=="New"
    assert (await store.get_secret(reference)).endswith("/old")


@pytest.mark.asyncio
async def test_invalid_webhook_and_enabling_without_secret_fail_closed():
    service=NotificationChannelService(Db(),InMemoryNotificationSecretStore(),"test")
    with pytest.raises(ValueError):await service.update_slack(uuid4(),SlackChannelUpdate(enabled=True,webhook_url="http://localhost/hook"))
    with pytest.raises(ValueError,match="required"):await service.update_slack(uuid4(),SlackChannelUpdate(enabled=True))


@pytest.mark.asyncio
async def test_delete_disables_before_secret_delete_and_removes_setting():
    user_id=uuid4();reference=slack_secret_reference(user_id,"test");setting=SimpleNamespace(id=uuid4(),user_id=user_id,channel_type="slack",enabled=True,secret_reference=reference)
    db=Db(setting);store=InMemoryNotificationSecretStore();await store.put_secret(reference,"secret")
    assert await NotificationChannelService(db,store,"test").delete_slack(user_id)
    assert not setting.enabled;db.delete.assert_awaited_once_with(setting)
    with pytest.raises(SecretNotFoundError):await store.get_secret(reference)


@pytest.mark.asyncio
async def test_resolver_filters_enabled_subscription_secret_and_user_in_query():
    user_id=uuid4();other=uuid4();store=InMemoryNotificationSecretStore()
    valid=SimpleNamespace(id=uuid4(),user_id=user_id,enabled=True,channel_type="slack",subscribed_event_types=["supplier_policy_review_changed"],secret_reference=slack_secret_reference(user_id,"test"))
    wrong=SimpleNamespace(id=uuid4(),user_id=other,enabled=True,channel_type="slack",subscribed_event_types=[],secret_reference=slack_secret_reference(other,"test"))
    await store.put_secret(valid.secret_reference,"secret")
    result=SimpleNamespace(scalars=lambda:SimpleNamespace(all=lambda:[valid,wrong]));db=SimpleNamespace(execute=AsyncMock(return_value=result))
    resolved=await NotificationChannelResolver(db,store).resolve(user_id,"supplier_policy_review_changed")
    assert resolved==[valid]
    sql=str(db.execute.await_args.args[0].compile(compile_kwargs={"literal_binds":True}))
    assert str(user_id).replace("-","") in sql
