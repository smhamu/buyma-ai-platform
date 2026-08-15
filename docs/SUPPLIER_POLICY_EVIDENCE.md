# Supplier Policy Evidence

## 1. Purpose

Supplier Policy Evidence records who checked a policy source, when it was checked, what it indicated, where the evidence came from, and why it matters. It preserves research history separately from the Supplier's current operational decision.

## 2. Evidence vs Policy

Evidence is an observed result. Supplier fields such as `terms_status`, `robots_status`, `vat_policy`, `ships_to_japan`, `official_api_available`, and `buyma_allowed_status` remain the human-approved current policy. Creating evidence never updates those fields. Operators review a mismatch and explicitly edit the Supplier if the operational policy should change.

## 3. Domain Model

`supplier_policy_evidence` stores supplier/owner IDs, evidence type and result, optional source metadata, notes, `checked_at`, the authenticated reviewer, a policy-only JSON snapshot, and immutable creation timestamps. The snapshot excludes credentials, tokens, cookies, API keys, general Supplier notes and product content.

## 4. Evidence Types

Supported types are `terms`, `robots`, `vat`, `shipping`, `official_api`, `buyma`, `ingestion`, `resale_restriction`, and `other`. String-backed validated values allow a future migration to extend this list without coupling it to PostgreSQL enum DDL.

## 5. Result semantics

`result` uses a controlled cross-policy vocabulary. It includes policy values such as `restricted`, `not_refunded`, and `unchecked`; capability values `supported`/`unsupported`; confirmation values; and ingestion modes. Shipping and official API booleans map to `supported` or `unsupported` for consistency checks. Results remain evidence and are not legal conclusions.

## 6. Immutability

The API provides create, list, latest-summary and detail operations only. There is no update or delete endpoint. Corrections are appended as new evidence, retaining the original record. Administrative hard deletion is intentionally absent in the MVP.

## 7. Latest Evidence

The latest record per evidence type is selected by `checked_at`, then `created_at`. The summary endpoint avoids joining full evidence history into Supplier lists.

## 8. Consistency

The service compares current Supplier policy with the latest evidence for terms, robots, VAT, shipping, official API and BUYMA. Matching values return `consistent=true`, mismatches return `false`, and missing evidence returns `null`.

## 9. Freshness

Every summary includes `age_days`. Clients may pass `max_age_days` to request an `is_stale` decision. No type-specific lifetime is embedded in the database or Frontend. Without a threshold, `is_stale` is null. This keeps future user/organization settings possible.

## 10. Review workflow

1. Add evidence from a source reviewed by the operator.
2. Inspect latest evidence and any `Review required` mismatch.
3. Decide whether the Supplier's current policy should change.
4. Explicitly edit the Supplier.
5. Reopen the summary to confirm `Up to date`.
6. Append later reviews; never replace earlier evidence.

## 11. Security

Source URLs reuse Research Ingestion URL normalization: only absolute HTTP(S), no userinfo, localhost, metadata host, private, loopback or link-local IP. Domain matching is intentionally not required because valid evidence can come from BUYMA, government or legal sources. Registration never fetches the URL. URL, title, excerpt, notes and query lengths are bounded; result values are whitelisted; timezone-aware timestamps more than five minutes in the future are rejected. Secrets, auth tokens and cookies must never be stored.

## 12. API

- `POST /suppliers/{supplier_id}/policy-evidence`
- `GET /suppliers/{supplier_id}/policy-evidence`
- `GET /suppliers/{supplier_id}/policy-evidence/latest`
- `GET /suppliers/{supplier_id}/policy-evidence/{evidence_id}`

List filters support type, result, checked range, text query, pagination and whitelisted sorting. All responses use the platform success envelope. Evidence inaccessible through Supplier ownership returns 404.

## 13. Frontend UX

The Suppliers page opens a Policy Evidence panel showing current policy, latest evidence, checked date/age, consistency text, append form and paginated newest-first history. External sources use `target="_blank"` with `rel="noopener noreferrer"`. The UI explicitly says adding evidence does not change policy. Color is not the only mismatch signal.

## 14. Relationship to Supplier Research

Research documents remain human-readable analysis. Evidence records are operator-attributed database history for a concrete Supplier. Product Purchase Restriction and availability remain separate product-level concepts.

## 15. Why existing research was not backfilled

Existing Hermès, CHANEL, Gucci, Prada, Saint Laurent, Bottega Veneta and LOEWE seed scripts are unchanged. Backfilling would require guessing the database Supplier, reviewer identity and exact check time, and some seeds may never have been run.

## 16. Future automated review notifications

The latest summary, `age_days`, optional stale evaluation and consistency flags provide the inputs for future scheduled reminders. No automatic fetch, policy mutation, Celery schedule, email, Slack or AI/legal classification is implemented now.
