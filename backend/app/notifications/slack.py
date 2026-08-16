from __future__ import annotations

import logging
import re
from urllib.parse import quote, urlparse

import httpx

from app.services.notification_outbox_consumer import DeliveryResult, OutboxDeliveryEvent

logger = logging.getLogger("buyma-ai-platform.notifications.slack")
# httpx's INFO request line contains the complete webhook path, which is a secret.
logging.getLogger("httpx").setLevel(logging.WARNING)


def validate_slack_webhook_url(webhook_url: str) -> str:
    parsed = urlparse(webhook_url)
    if (
        parsed.scheme != "https" or parsed.hostname != "hooks.slack.com"
        or parsed.username or parsed.password or not parsed.path.startswith("/services/")
    ):
        raise ValueError("Slack webhook must be an HTTPS hooks.slack.com Incoming Webhook URL.")
    return webhook_url


def _plain(value: object) -> str:
    return re.sub(r"[\r\n\t]+", " ", str(value or "")).strip()


def _mrkdwn(value: object) -> str:
    return _plain(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _label(value: object) -> str:
    return _plain(value).replace("_", " ").title()


def format_supplier_policy_review_message(
    event: OutboxDeliveryEvent, *, frontend_base_url: str | None = None
) -> dict:
    payload = event.payload
    supplier = _mrkdwn(payload.get("supplier_name") or "Unknown supplier")
    before = _label(payload.get("from_status") or "not evaluated")
    after = _label(payload.get("to_status") or "unknown")
    changed = ", ".join(_label(item) for item in payload.get("changed_evidence_types") or []) or "None"
    occurred = _plain(payload.get("occurred_at") or "Unknown")
    text = f"Supplier Policy Review changed: {supplier} ({before} -> {after})"
    blocks: list[dict] = [
        {"type": "header", "text": {"type": "plain_text", "text": "Supplier Policy Review changed"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Supplier:*\n{supplier}"},
            {"type": "mrkdwn", "text": f"*Status:*\n{_mrkdwn(before)} → {_mrkdwn(after)}"},
            {"type": "mrkdwn", "text": f"*Changed:*\n{_mrkdwn(changed)}"},
            {"type": "mrkdwn", "text": f"*Occurred:*\n{_mrkdwn(occurred)}"},
        ]},
    ]
    if frontend_base_url:
        base = frontend_base_url.rstrip("/")
        supplier_id = quote(str(payload.get("supplier_id") or event.resource_id), safe="")
        review_url = f"{base}/supplier-policy-review/{supplier_id}"
        blocks.append({
            "type": "actions",
            "elements": [{
                "type": "button", "text": {"type": "plain_text", "text": "Open review"},
                "url": review_url,
            }],
        })
    return {"text": text, "blocks": blocks}


class SlackNotificationAdapter:
    def __init__(
        self, webhook_url: str, *, frontend_base_url: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self._webhook_url = validate_slack_webhook_url(webhook_url)
        self._frontend_base_url = frontend_base_url
        self._http_client = http_client

    async def deliver(self, event: OutboxDeliveryEvent) -> DeliveryResult:
        if event.event_type != "supplier_policy_review_changed":
            return DeliveryResult(
                success=False, retryable=False, error="Unsupported notification event.",
                safe_error_code="slack_unsupported_event",
            )
        message = format_supplier_policy_review_message(
            event, frontend_base_url=self._frontend_base_url
        )
        try:
            if self._http_client is not None:
                response = await self._http_client.post(self._webhook_url, json=message)
            else:
                timeout = httpx.Timeout(10.0, connect=3.0, read=7.0)
                async with httpx.AsyncClient(
                    timeout=timeout, follow_redirects=False, verify=True, trust_env=True
                ) as client:
                    response = await client.post(self._webhook_url, json=message)
        except httpx.RequestError:
            logger.warning("Slack delivery transport failure outbox_id=%s event_type=%s", event.id, event.event_type)
            return DeliveryResult(
                success=False, retryable=True, error="Slack transport failure.",
                safe_error_code="slack_transport_error",
            )
        status = response.status_code
        logger.info(
            "Slack delivery completed outbox_id=%s event_type=%s supplier_id=%s status=%s",
            event.id, event.event_type, event.resource_id, status,
        )
        if 200 <= status < 300:
            return DeliveryResult(success=True, provider_status_code=status)
        retry_after = None
        if status == 429:
            try:
                retry_after = max(0, int(response.headers.get("Retry-After", "0")))
            except ValueError:
                retry_after = None
        retryable = status == 408 or status == 429 or status >= 500
        return DeliveryResult(
            success=False, retryable=retryable,
            error="Slack provider rejected delivery.", provider_status_code=status,
            retry_after_seconds=retry_after,
            safe_error_code=f"slack_http_{status}",
        )
