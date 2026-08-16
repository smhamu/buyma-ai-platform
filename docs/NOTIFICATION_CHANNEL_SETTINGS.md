# User Notification Channel Settings

## Architecture

`NotificationOutbox` is the application event awaiting expansion. `NotificationChannelSetting` is one user's subscription and secret reference. Expansion resolves only enabled, configured settings owned by the Outbox owner and creates zero-to-many `NotificationDelivery` rows. Delivery state, retry, provider status, and idempotency belong to Delivery, not Outbox.

An Outbox becomes `expanded` after at least one Delivery is created. With no subscribed channel it becomes `cancelled`; this is a valid no-channel outcome and is not retried. The unique `(outbox_id, channel_setting_id)` constraint and `ON CONFLICT DO NOTHING` make expansion idempotent. Slack and future Email settings can therefore produce independent Deliveries from one Outbox.

## Slack settings and UI

- `GET /notification-channels/slack`
- `PUT /notification-channels/slack`
- `DELETE /notification-channels/slack`
- Frontend: `/notification-settings`

Responses contain enabled/configured state, destination label, and subscriptions. They never contain the webhook or secret reference. Updating metadata without a webhook preserves the current secret. Removal first disables the setting and cancels pending/processing Deliveries, then removes the secret and setting. The only MVP event is `supplier_policy_review_changed`; an empty subscription means no delivery.

## Secret Store

Webhook plaintext is never stored in PostgreSQL, Outbox, or Delivery. PostgreSQL stores only:

```text
/buyma-ai/<environment>/users/<uuid>/notifications/slack/webhook
```

Production requires `NOTIFICATION_SECRET_STORE=ssm` and EC2 Instance Profile credentials. Grant narrowly scoped `ssm:GetParameter`, `ssm:PutParameter`, and `ssm:DeleteParameter` for `/buyma-ai/production/users/*`. SecureString is resolved immediately before delivery so rotation takes effect without snapshots. SSM unavailability is retryable; a missing parameter is a permanent configuration error.

The Production proxy permits encrypted CONNECT to regional `ssm.<region>.amazonaws.com`, `hooks.slack.com`, and `api.openai.com`. IMDS `169.254.169.254` bypasses the proxy; the EC2 metadata hop limit must permit container access. A private SSM VPC endpoint is recommended for later hardening.

External secret writes and DB commits cannot be atomic. PUT compensates a DB failure by restoring/deleting the new secret. DELETE commits `enabled=false` before external deletion, leaving a safe retryable state if SSM is unavailable.

## Delivery lifecycle and isolation

Celery schedules `notification_outbox.expand` and `notification_delivery.consume`. Delivery uses `FOR UPDATE SKIP LOCKED`, processing leases, stuck recovery, exponential backoff, `Retry-After`, and max attempts. One failure does not stop the batch. Owner constraints bind setting, Outbox, Delivery, and resolved secret to the same user.

`GET /notification-deliveries`, `GET /notification-deliveries/stats`, and `POST /notification-deliveries/{id}/retry` are owner-scoped. Admin may inspect/retry all metadata but cannot read secrets.

## Legacy and future channels

`SLACK_WEBHOOK_URL` and `NOTIFICATION_DELIVERY_PROVIDER` remain only for rollback compatibility. New scheduled tasks never silently fall back to the environment webhook. Keep that legacy provider disabled and remove it after the rollback window.

Email and LINE values reserve future schema evolution, but adapters/APIs are not implemented. Slack OAuth, channel discovery, notification center, read state, acknowledgement, and automatic policy/evidence changes are also out of scope.
