# Product Purchase Restriction

## Purpose

`purchase_restriction` records how an individual researched product can be purchased. It is independent from `availability_status`: stock can be available while purchase still requires a boutique or client advisor. `notify_me` therefore remains an availability observation (normally out of stock), not a purchase restriction.

Brand policy is the default online-purchase policy and `BrandCategoryPolicy` may override it for one category. A product restriction never overrides either policy; it is an additional, final policy gate. This distinction is needed for Gucci and Prada research, where products in the same brand/category can have different purchase paths.

## Values

| Value | Meaning | Ready for listing |
|---|---|---|
| `normal` | Ordinary online purchase was verified | Allowed by this gate |
| `pre_order` | Order precedes normal availability | Rejected pending an explicit BUYMA policy |
| `personalized` | Product is customized | Rejected |
| `made_to_order` | Product is produced on request | Rejected |
| `client_advisor_only` | A client advisor is required | Rejected |
| `boutique_only` | Purchase is limited to a boutique | Rejected |
| `research_only` | Evidence may be researched but not listed | Rejected |
| `unknown` / database `NULL` | Purchase route has not been verified | Rejected (fail closed) |

Existing rows remain `NULL`; the migration deliberately does not infer `normal`. New API and ingestion records default to `unknown` unless a researcher supplies a value.

## Ready-for-listing evaluation

The checks run in this order:

1. supplier BUYMA prohibition;
2. supplier shipping to Japan;
3. brand/category research enablement;
4. resolved category override or brand default policy;
5. online-purchase availability flag;
6. stock availability;
7. product purchase restriction (the final product-policy gate).

A non-normal product restriction returns `PRODUCT_PURCHASE_RESTRICTED` with a user-facing reason. Existing error codes remain in use for the other gates.

## Research ingestion

Manual URL registration accepts an optional restriction and naturally defaults to `unknown`. CSV accepts an optional `purchase_restriction` column; an invalid non-empty value fails only that row. Source-to-candidate conversion copies the normalized product restriction. No external fetch, classification, or inference is performed.

## Inventory boundary

Future inventory monitoring should update `availability_status` and observations such as “notify me”. It must not infer or overwrite `purchase_restriction`; changing a purchase route requires separate research evidence and review.
