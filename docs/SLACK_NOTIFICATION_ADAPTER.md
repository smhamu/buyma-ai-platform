# Slack Notification Adapter

## Purpose and architecture

The Slack adapter sends only `supplier_policy_review_changed` events from the existing transactional Outbox. It does not modify review state, supplier policy, or evidence. Celery claims an event, passes an immutable delivery event to the adapter, and the Consumer alone records delivery/retry/failure.

Incoming Webhook was selected for the MVP because it needs no bot installation or OAuth scopes and fits one environment-wide operational destination. Slack Web API would be appropriate later for dynamic channels, message updates, richer provider state, or bot identity control.

## Configuration and secrets

```env
NOTIFICATION_OUTBOX_CONSUMER_ENABLED=true
NOTIFICATION_DELIVERY_PROVIDER=slack
SLACK_WEBHOOK_URL=
PRODUCTION_BASE_URL=https://production.example
```

Store `SLACK_WEBHOOK_URL` in the EC2 secret source/SSM flow and inject it only as an environment variable. Never store it in the database, Outbox payload, API response, UI, or logs. Slack mode fails closed when the URL is missing or is not an HTTPS `hooks.slack.com/services/...` Incoming Webhook. Production rejects the noop provider and never falls back to it.

Production egress permits HTTPS CONNECT only to `api.openai.com` and `hooks.slack.com`; the proxy has no host port and access logging remains disabled.

## Message format and safety

Messages contain a plain-text fallback and small Block Kit payload: header, supplier, status transition, changed evidence types, occurrence time, and an optional environment-derived review link. Supplier/payload text is normalized and Slack metacharacters are escaped. The webhook URL, full Outbox payload, provider response body, and idempotency key are not included in messages or logs.

## Response classification

- `2xx`: delivered.
- `408`, `429`, `5xx`, timeout, connection error: retryable.
- Other `4xx`: permanent failure.
- Unknown event types: permanent unsupported-event failure.

The adapter performs exactly one HTTP request and does not retry internally. Outbox exponential backoff remains authoritative. A valid `Retry-After` on `429` is applied as a minimum delay, so the later of Consumer backoff and Slack guidance is used. Only safe error codes such as `slack_http_429` are persisted; raw response bodies are discarded.

## Idempotency limitation

The adapter receives the Outbox dedupe key as an idempotency key, preserving the channel contract, but Incoming Webhooks do not provide a strong provider-side idempotency guarantee. Claiming and leases minimize duplicates; exactly-once delivery cannot be guaranteed if Slack accepts a request and the worker fails before recording `delivered`.

## Production enablement

1. Create a dedicated operational Incoming Webhook without pasting it into chat or logs.
2. Store it as a protected Production secret and regenerate `.env.production` securely.
3. Set the provider to `slack` and enable the Consumer.
4. Validate Squid configuration and restart the egress proxy, Celery Worker, and Beat.
5. Create a controlled review transition and confirm Outbox state and the Slack message.
6. Monitor pending/processing/failed counts and oldest pending age.

No automatic live webhook test is included. A development webhook may be verified manually only after code deployment. User-specific webhook settings are now the source of truth; per-user Slack OAuth, channel discovery, acknowledgements, and notification-center features remain future work. The environment webhook selector is retained only for rollback compatibility and is never a silent fallback.
