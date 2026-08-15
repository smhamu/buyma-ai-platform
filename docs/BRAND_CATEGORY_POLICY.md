# Brand Category Purchase Policy

## Why brand-level policy was insufficient

`Brand.online_purchase_policy` remains the fallback, but one value cannot represent the reviewed behavior. Hermès can remain conservative at brand level, CHANEL differs materially between boutique-led Fashion and online Fragrance/Beauty/Eyewear, and Gucci has broad online purchasing with product-level exceptions.

## Category Master

`ProductCategory` is global and uses a unique lowercase snake-case code. The initial flat taxonomy is Handbags, Small Leather Goods, Shoes, Ready-to-wear, Accessories, Jewelry, Watches, Eyewear, Fragrance and Beauty. A hierarchy is deliberately omitted. Makeup and Skincare can later become children of Beauty if actual filtering and reporting requirements justify it.

Categories are seeded idempotently. Existing rows are never overwritten.

## Override and fallback

`BrandCategoryPolicy` is unique for `(brand_id, category_id)` and stores purchase policy, research enablement, evidence notes and `checked_at`.

Resolution is centralized:

1. use an active Category override when `category_id` is supplied;
2. otherwise use `Brand.online_purchase_policy` and `Brand.is_research_enabled`.

Callers must not reimplement fallback logic.

## Ready for Listing

Candidate create, calculate and update resolve the effective policy. `research_only` and `boutique_only` prevent `ready_for_listing`. A category-derived rejection uses `CATEGORY_PURCHASE_RESTRICTED`; existing supplier, stock, shipping and brand checks remain in effect.

## Ingestion

Manual URL sources accept an optional `category_id`. CSV accepts an optional `category_code`; omission remains backward compatible and an unknown non-empty code fails only that row. Source-to-Candidate conversion carries `category_id` unchanged. Existing free-text Candidate `category` remains for compatibility but is not backfilled or guessed.

## CHANEL seed

Only documented overrides are seeded:

- Handbags, Small Leather Goods, Shoes: `boutique_only`
- Fragrance, Beauty, Eyewear: `normal`

Hermès and Gucci receive no inferred overrides. The CHANEL seed fails closed when Brand or required Categories are missing and never updates existing policies.

## Product-level restrictions

Sold out, pre-order, personalized, made-to-order and Client Advisor-only are product availability/purchase conditions. They are not Category policies and are not modeled in this change.

## Operations

Run migration first, then global masters:

```bash
alembic upgrade head
python scripts/seed_product_categories.py
python scripts/seed_luxury_brands.py
python scripts/seed_chanel_category_policies.py
```

Reconfirm policy evidence periodically using `checked_at`; do not infer new overrides from brand reputation or technical page structure.
