import logging
from uuid import uuid4

import httpx
import pytest

from app.notifications.slack import SlackNotificationAdapter, format_supplier_policy_review_message
from app.services.notification_outbox_consumer import OutboxDeliveryEvent
from app.services.notification_outbox_consumer import NotificationOutboxConsumerService
from types import SimpleNamespace
from unittest.mock import AsyncMock

WEBHOOK = "https://hooks.slack.com/services/T000/B000/secret-value"


def event(event_type="supplier_policy_review_changed"):
    supplier_id = uuid4()
    return OutboxDeliveryEvent(
        id=uuid4(), event_type=event_type, resource_type="supplier", resource_id=supplier_id,
        payload={
            "supplier_id": str(supplier_id),
            "supplier_name": "Shop <admin> & team\n<!channel>",
            "from_status": "up_to_date", "to_status": "review_due",
            "changed_evidence_types": ["terms", "buyma"],
            "occurred_at": "2026-08-16T00:00:00+00:00",
        },
        idempotency_key="secret-dedupe-key",
    )


def client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_formatter_escapes_untrusted_text_and_has_fallback_and_action():
    message = format_supplier_policy_review_message(event(), frontend_base_url="https://production.example")
    serialized = str(message)
    assert "&lt;admin&gt; &amp; team &lt;!channel&gt;" in serialized
    assert "Supplier Policy Review changed" in message["text"]
    assert "https://production.example/supplier-policy-review/" in serialized
    assert "secret-dedupe-key" not in serialized


@pytest.mark.asyncio
async def test_success_uses_one_request_and_does_not_log_webhook(caplog):
    requests = []
    async with client(lambda request: requests.append(request) or httpx.Response(200, text="ok")) as http:
        adapter = SlackNotificationAdapter(WEBHOOK, http_client=http)
        with caplog.at_level(logging.INFO):
            result = await adapter.deliver(event())
    assert result.success and result.provider_status_code == 200
    assert len(requests) == 1
    assert "secret-value" not in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [408, 500, 503])
async def test_retryable_http_failures(status):
    async with client(lambda _: httpx.Response(status)) as http:
        result = await SlackNotificationAdapter(WEBHOOK, http_client=http).deliver(event())
    assert not result.success and result.retryable
    assert result.safe_error_code == f"slack_http_{status}"


@pytest.mark.asyncio
async def test_rate_limit_carries_retry_after_without_body():
    async with client(lambda _: httpx.Response(429, headers={"Retry-After": "37"}, text="private")) as http:
        result = await SlackNotificationAdapter(WEBHOOK, http_client=http).deliver(event())
    assert result.retryable and result.retry_after_seconds == 37
    assert "private" not in (result.error or "")


@pytest.mark.asyncio
async def test_permanent_4xx_and_unsupported_event():
    async with client(lambda _: httpx.Response(400, text="do not persist")) as http:
        result = await SlackNotificationAdapter(WEBHOOK, http_client=http).deliver(event())
        unsupported = await SlackNotificationAdapter(WEBHOOK, http_client=http).deliver(event("unknown"))
    assert not result.retryable and result.safe_error_code == "slack_http_400"
    assert not unsupported.retryable and unsupported.safe_error_code == "slack_unsupported_event"


@pytest.mark.asyncio
async def test_timeout_is_retryable():
    def timeout(request):
        raise httpx.ReadTimeout("timeout", request=request)
    async with client(timeout) as http:
        result = await SlackNotificationAdapter(WEBHOOK, http_client=http).deliver(event())
    assert result.retryable and result.safe_error_code == "slack_transport_error"


@pytest.mark.parametrize("url", ["", "http://hooks.slack.com/services/a", "https://example.com/services/a"])
def test_malformed_or_non_slack_webhook_is_rejected(url):
    with pytest.raises(ValueError):
        SlackNotificationAdapter(url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "failure_outcome", "delivered", "retried", "failed"),
    [(200, None, 1, 0, 0), (429, "retried", 0, 1, 0), (400, "failed", 0, 0, 1)],
)
async def test_slack_adapter_consumer_state_integration(
    status, failure_outcome, delivered, retried, failed
):
    delivery_event = event()
    row = SimpleNamespace(
        id=delivery_event.id, event_type=delivery_event.event_type,
        resource_type=delivery_event.resource_type, resource_id=delivery_event.resource_id,
        payload=delivery_event.payload, dedupe_key=delivery_event.idempotency_key,
    )
    db = SimpleNamespace()
    consumer = NotificationOutboxConsumerService(db)
    consumer.claim = AsyncMock(return_value=[row])
    consumer.mark_delivered = AsyncMock()
    consumer.mark_failure = AsyncMock(return_value=failure_outcome)
    async with client(lambda _: httpx.Response(status, headers={"Retry-After": "20"})) as http:
        result = await consumer.dispatch_batch(
            SlackNotificationAdapter(WEBHOOK, http_client=http), 1
        )
    assert (result.delivered, result.retried, result.failed) == (delivered, retried, failed)
