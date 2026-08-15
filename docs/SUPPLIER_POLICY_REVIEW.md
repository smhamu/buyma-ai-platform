# Supplier Policy Review

## Purpose

Supplier Policy Review turns immutable Supplier Policy Evidence into a user-owned review queue. It identifies policies that need human attention; it never changes Supplier policy, fetches evidence, disables a Supplier, or makes legal/BUMYA decisions.

## Review status and priority

Each tracked type (`terms`, `robots`, `vat`, `shipping`, `official_api`, `buyma`) is evaluated independently. A missing required type is `no_evidence`; conflicting current policy and latest evidence is `inconsistent`; consistent evidence older than its configured threshold is `review_due`; otherwise it is `up_to_date`. Overall precedence is inconsistent, review due, no evidence, then up to date.

Priority is intentionally simple: inconsistent is critical; missing/stale Terms or BUYMA is high; other review work is medium; up-to-date is normal.

## Thresholds and required evidence

Settings belong to one User and cannot be read or changed by another User. Defaults are conservative operational starting points: Terms, robots, VAT and shipping 180 days, BUYMA 90 days, official API 365 days. A nullable threshold disables freshness expiry for that type. Terms, robots, VAT, shipping and BUYMA are required by default; official API is optional. Values are editable from the dashboard and validated from 1 through 3650 days.

## Review queue and human workflow

`GET /supplier-policy-review` computes the current queue from Suppliers and latest evidence without loading full evidence histories. It supports status, evidence type, country, supplier type, brand, keyword, pagination and documented sorting. `GET /supplier-policy-review/{supplier_id}` returns the per-type detail. The dashboard links to immutable evidence history and Supplier editing.

Adding evidence does not complete a review when it conflicts with current policy. For example, Unknown current Terms plus Restricted evidence remains inconsistent until a human deliberately updates the Supplier policy. A later stale date returns it to review due.

## Notifications

For this MVP, the Review Queue is the in-app notification mechanism. No separate Notification table or Celery notification producer was added because the repository has no existing notification lifecycle, and persisting duplicate alerts would add acknowledgement/state semantics beyond this release. The dynamic queue has one current row per Supplier and therefore cannot generate daily duplicates. A future notification outbox should deduplicate on owner, supplier, evidence type and status transition, and permit a new notification only after resolution and a later transition.

Email, Slack, LINE and webhooks are not implemented.

## Security and performance

Supplier ownership/administrator access remains authoritative and inaccessible detail IDs return Not Found. Required types are a whitelist and thresholds are bounded. Evidence URLs are not accessed. Queue responses contain no credentials or source excerpts. The existing `(supplier_id, evidence_type, checked_at)` index supports latest evidence lookup; full histories are not joined.

## Future work

Before external notifications, add a durable transition/outbox model, read/acknowledgement semantics, delivery retries and recipient preferences. Organization-scoped settings can replace User settings if an Organization domain is introduced.
