# Supplier Policy Review State, Transitions, and Outbox

## Current State vs Transition

`supplier_policy_review_states` stores the last observed current review result for one Supplier. It includes the overall status, issue types, per-type statuses, evaluation time, and a monotonically increasing version. It is not history.

`supplier_policy_review_transitions` is append-only history. A transition is written when either the overall status or any per-type status changes. Initial evaluation is recorded as `null -> current`, but never generates a notification. The `(supplier_id, state_version)` constraint prevents two histories for one state version.

## Review Queue vs Outbox

The Review Queue remains the authoritative view of what needs attention now. A Transition records that state changed. `notification_outbox` records delivery intent for a non-initial transition. These concepts must not be used interchangeably.

## Transition and notification rules

Examples include no evidence to inconsistent, inconsistent to up to date, up to date to review due, review due to inconsistent, and recovery transitions. Recovery is intentionally emitted so future channels can clear or resolve an earlier alert. A repeated identical evaluation only updates `evaluated_at`; it creates neither Transition nor Outbox. A change limited to one Evidence Type is still recorded even if the overall status stays unchanged.

Every non-initial Transition currently produces one `supplier_policy_review_changed` event. The payload contains only Supplier ID/name, previous/new status, changed type names, and occurrence time. It excludes raw evidence, policy snapshots, notes, credentials, tokens, and API keys.

## Transactional outbox and dedupe

State update, Transition, and Outbox insertion use one database commit. Evidence creation uses the same transaction as those records. Failed commits are rolled back. Supplier policy updates are committed by the existing CRUD service and then evaluated; the derived State/Transition/Outbox remain atomic with each other.

An Outbox row has a unique Transition foreign key and a unique `supplier-policy-review:<transition-id>` dedupe key. Existing State rows are locked with `SELECT FOR UPDATE`. Initial-state races are protected by unique Supplier State and retried once. This makes repeated or concurrent evaluation unlikely to create duplicate Transitions or events.

## Evaluation triggers

- Supplier creation initializes State and an initial Transition without Outbox.
- Evidence creation evaluates transactionally after the Evidence is flushed.
- Supplier policy update evaluates after the existing update flow.
- Celery Beat evaluates every active Supplier hourly in 100-item processing batches.
- Settings updates do not synchronously recalculate all Suppliers. The next scheduled evaluation applies the changed thresholds/required types.

No evaluation performs external HTTP access, generates Evidence, changes Supplier policy, disables a Supplier, or performs legal/BUMYA classification.

## Outbox API

`GET /supplier-policy-review/{supplier_id}/transitions` returns newest-first history after Supplier ownership/administrator authorization. `GET /notification-outbox` returns only the authenticated owner's events and supports status, event type, resource ID, date, and pagination filters.

## Future consumer and retry model

A future Email, Slack, LINE, webhook, or in-app consumer should:

1. claim available `pending` rows using database locking/skip-locked;
2. atomically set them to `processing` and increment `attempt_count`;
3. deliver to the configured channel;
4. set success to `delivered` with `processed_at`;
5. set a retryable failure back to `pending` with a redacted `last_error` and future `available_at`;
6. set terminal failures to `failed` after a configured retry limit.

Consumers must be idempotent by Outbox ID/dedupe key and must never place secrets in status or error fields. Consumer claiming and delivery are intentionally not implemented in this phase.

## Security

Transition history follows Supplier ownership and returns Not Found for inaccessible resources. Outbox list is owner-scoped, including for administrators. Event/resource types are fixed by application code, payload shape is minimal, and no source URL is fetched. Database columns and API schemas whitelist statuses and event types.
