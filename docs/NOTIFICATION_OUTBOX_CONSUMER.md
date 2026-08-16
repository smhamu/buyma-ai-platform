# Notification Outbox Consumer

## Purpose and safety boundary

The consumer delivers the existing supplier policy review outbox without changing review state or supplier policy. Email, Slack, and LINE delivery are intentionally not implemented. Production defaults to `NOTIFICATION_OUTBOX_CONSUMER_ENABLED=false` and `NOTIFICATION_OUTBOX_ADAPTER=disabled`; the noop adapter is rejected in production so an event cannot be falsely marked delivered.

## Claim and lease

One database transaction first recovers expired processing leases, then selects eligible rows using `FOR UPDATE SKIP LOCKED`. Eligible means `status=pending` and `available_at <= now`. Claimed rows become `processing`, increment `attempt_count`, and receive `processing_started_at` and `lease_expires_at`. Multiple workers therefore claim disjoint batches. A worker crash leaves a lease which is recovered by a later claim after `NOTIFICATION_OUTBOX_LEASE_SECONDS`.

## Delivery lifecycle

- Success: `delivered`, `processed_at` set, lease cleared.
- Retryable failure below the limit: `pending`, lease cleared, `available_at` moved by capped exponential backoff.
- Non-retryable failure or attempt limit: `failed`, which is the dead-letter-equivalent state.
- Adapter exceptions are converted to event failures; another event in the batch is still processed.
- The channel adapter receives `dedupe_key` (falling back to the outbox UUID) as its idempotency key. A future real adapter must pass this key to the provider and persist/provider-check idempotency where supported. Database claiming minimizes duplicates but cannot alone guarantee exactly-once delivery after an external success followed by a worker crash.

Celery task retry is disabled (`max_retries=0`). Event retry is exclusively controlled by outbox state and `available_at`.

## Monitoring and administration

- `GET /notification-outbox`: owner-scoped for normal users; administrators can inspect all events.
- `GET /notification-outbox/stats`: pending, processing, delivered, failed and cancelled counts plus oldest pending timestamp/age. Normal users see their own events; administrators see global values.
- `POST /notification-outbox/{id}/retry`: only a failed event may be requeued. Owners may retry their own event and administrators may retry any event. Attempts and terminal fields are reset for a deliberate new retry cycle.

Error text is truncated and common bearer/OpenAI-key forms are redacted. Adapters must return operational errors only and must never include notification bodies, credentials, or authorization headers.

## Configuration

`NOTIFICATION_OUTBOX_BATCH_SIZE`, `NOTIFICATION_OUTBOX_MAX_ATTEMPTS`, `NOTIFICATION_OUTBOX_BASE_BACKOFF_SECONDS`, `NOTIFICATION_OUTBOX_MAX_BACKOFF_SECONDS`, and `NOTIFICATION_OUTBOX_LEASE_SECONDS` tune processing. Keep delivery disabled until a reviewed real adapter exists. The beat task may run while disabled; it returns without accessing or claiming the database.

## Adding a real channel

Implement `NotificationChannelAdapter.deliver(OutboxDeliveryEvent) -> DeliveryResult`, map only the required safe payload, use `event.idempotency_key`, configure bounded network timeouts, and avoid logging headers/body. Add adapter contract, retry classification, provider idempotency, and integration tests before allowing it in production.
