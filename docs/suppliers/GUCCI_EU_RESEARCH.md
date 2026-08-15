# Gucci EU Official Online Supplier Research

Research date: 2026-08-15

## Summary

Gucci operates localized official online stores for France, Germany, Italy and Spain. Official FAQ and sales terms confirm EUR prices, broad online product availability, product codes, availability states and VAT-inclusive prices. The reviewed EU storefronts serve European delivery destinations; Japan is a separate shopping region, so an EU-locale order must not be assumed to ship to Japan.

The website Terms restrict the site to private, personal and non-commercial use and restrict reproduction or reuse of its content. No permission for automated commercial collection and no documented public Product API were found. A single, low-volume request to `robots.txt` timed out and was not retried or bypassed. Therefore all four Suppliers start as `url_manual`, `automated_fetch_enabled=false`, `terms_status=restricted`, and `robots_status=unknown`.

## Country comparison

| Country | Official URL | Currency | Online purchase | EU-locale delivery to Japan | VAT | Initial source policy |
|---|---|---|---|---|---|---|
| France | `https://www.gucci.com/fr/fr/` | EUR | Broad, product-dependent | No; Japan is a separate region | Included; online tax refund unavailable | `url_manual` |
| Germany | `https://www.gucci.com/de/de/` | EUR | Broad, product-dependent | No; Japan is a separate region | Included; online tax refund unavailable | `url_manual` |
| Italy | `https://www.gucci.com/it/it/` | EUR | Broad, product-dependent | No; Japan is a separate region | Included; online tax refund unavailable | `url_manual` |
| Spain | `https://www.gucci.com/es/es/` | EUR | Broad, product-dependent | No; Japan is a separate region | Included; online tax refund unavailable | `url_manual` |

`ships_to_japan=false` represents shipping from these EU storefronts, not whether Gucci has a Japanese storefront. Gucci's FAQ lists Japan as a separate card/shipping region and lists EU-locale delivery destinations separately.

## Category purchase matrix

Gucci's EU FAQ says products from all categories are offered online, including bags, accessories, shoes, jewelry, decor, makeup and ready-to-wear. It also identifies watches, fragrances, cosmetics and eyewear as product categories. Availability remains product-specific.

| Category | Listing/detail | EUR price | Online purchase | Exceptions to retain |
|---|---|---|---|---|
| Handbags | Yes | Yes | Generally available | sold out, pre-order, personalized, client-advisor-only |
| Small leather goods | Yes | Yes | Generally available | product stock and personalization |
| Shoes | Yes | Yes | Generally available | size/stock dependent |
| Ready-to-wear | Yes | Yes | Generally available | size/stock dependent |
| Accessories | Yes | Yes | Generally available | product stock dependent |
| Jewelry | Yes | Yes | Available for eligible items | product stock and special-order constraints |
| Watches | Yes | Yes | Available for eligible items | product stock and special-order constraints |
| Eyewear | Yes | Yes | Generally available | product stock dependent |
| Beauty | Yes | Yes | Generally available | product stock dependent |
| Fragrance | Yes | Yes | Generally available | product stock dependent |

Observed availability labels include available, available in 1–3 weeks, pre-order, personalized and sold out online. Some exceptional listings direct customers to a Client Advisor. These are candidate-level conditions, not evidence that an entire category is boutique-only.

## Product data availability

Official indexed listing and product pages exposed the following human-visible fields:

- product name and canonical-looking locale URL
- style/product code (for example, the product page displays a `Style` value)
- EUR price
- online availability or sold-out wording
- color/material descriptions
- size or personalization choices where applicable
- multiple product images
- related variants represented by distinct product/style identifiers

The locale URL is stable enough for manual source registration, but canonical link markup was not independently verified. Availability must be captured as checked-at evidence and not treated as durable inventory.

## JSON-LD / structured data

Search indexing proves that product fields are publicly rendered, but does not prove the presence or stability of `Product`, `Offer`, SKU, price, currency or availability JSON-LD. Raw product HTML was not repeatedly fetched after the official host refused/timed out on direct access. JSON-LD is therefore `unconfirmed`, and `structured_data` is not selected.

Technical discoverability alone would not override the Terms restriction. Written permission is required before considering automated structured-data ingestion.

## Official / public Product API

No documented Gucci public Product, price, inventory, developer, affiliate feed or supported GraphQL API was found. Browser-internal endpoints, if observed in a normal browser, are not public APIs and must not be used without authorization.

Set `official_api_available=false`.

## Terms

The localized legal pages state that the website and its collected/organized data, product content, images and software are protected. The site is described as exclusively for private, personal, non-commercial use; reproduction, publication, distribution, modification, derivative use and sale-related reuse are restricted. Sales are reserved to consumers acting outside commercial or professional activity, and Gucci may reject suspected commercial purchases.

These clauses create both ingestion and resale concerns. Set `terms_status=restricted`; do not automate collection or treat the official store as confirmed for commercial sourcing without written/legal review.

## robots.txt

`https://www.gucci.com/robots.txt` was requested once on 2026-08-15. The request timed out with no content, and no retry, alternate user agent, browser automation, proxy or bypass was used. Rules therefore remain unverified.

Set `robots_status=unknown`. Recheck manually and preserve the retrieved evidence before any automation review. A permissive robots file would not override the Terms.

## VAT

All four localized FAQ pages state that displayed prices include VAT and that tax refunds are currently unavailable for Gucci.com purchases. Seed policy is therefore:

```text
vat_policy=not_refunded
vat_rate=null
```

This explicitly prevents automatic export-price deduction. `included` alone would also not prove export exclusion; here the stronger official statement that online tax refunds are unavailable supports `not_refunded`.

## Shipping

EU storefront shipping information covers European destinations (and separately listed supported regions). Japan is identified as a separate shopping/payment region rather than an EU storefront destination. The four EU Supplier seeds therefore use `ships_to_japan=false`.

This remains subject to periodic checkout and FAQ verification. It does not claim Gucci lacks Japan sales.

## Recommended Supplier Policy

```text
supplier_type=authorized_retailer
default_currency=EUR
ships_to_japan=false
vat_policy=not_refunded
vat_rate=null
japan_shipping_cost=null
buyma_allowed_status=unchecked
research_status=reviewing
is_active=true
ingestion_source_type=url_manual
automated_fetch_enabled=false
terms_status=restricted
robots_status=unknown
official_api_available=false
parser_key=null
request_interval_seconds=null
```

## Brand Master policy assessment

Brand Master currently stores Gucci as `online_purchase_policy=unknown`. Among the existing enums, `limited` is the closest recommendation: broad categories can be purchased online, but availability is product-specific and the official sales terms restrict purchasing to personal/non-commercial consumers. This document does not modify Brand Master.

`normal` would overstate commercial sourcing suitability. `category_limited` is less accurate than for CHANEL because Gucci's FAQ expressly covers broad categories. `boutique_only` and `research_only` understate the observable online store, though manual research remains the safe ingestion policy.

## Three-brand comparison

This comparison uses only the existing Hermès and CHANEL research documents plus this review.

| Brand | Observed online pattern | Terms | robots | Initial ingestion | Brand-policy conclusion |
|---|---|---|---|---|---|
| Hermès | Online product research with unresolved purchase/export constraints | restricted | allowed (at review date) | `url_manual` | Existing `research_only` retained |
| CHANEL | Strong category split: Fashion/boutique vs Beauty/Eyewear online | restricted | restricted | `url_manual` | Existing `research_only`; category policy needed |
| Gucci | Broad category online purchase, product-level exceptions | restricted | unknown | `url_manual` | `limited` is closest; no Brand update in this task |

The contrast—especially CHANEL's category split versus Gucci's product-level exceptions—supports a future category-level purchase-policy domain. It should supplement, not silently replace, Brand policy and should carry evidence/check dates. No such domain is implemented here.

## Seed

`backend/scripts/seed_gucci_eu_suppliers.py` asks for an active Admin owner and links four country Suppliers to the global `gucci` Brand.

```bash
cd backend
python scripts/seed_luxury_brands.py
python scripts/seed_gucci_eu_suppliers.py
```

The seed is idempotent by owner and Supplier name. Existing records are not updated or overwritten. A missing Gucci Brand fails closed. The seed performs no external HTTP requests and was not executed against a database during this work.

## BUYMA considerations

- Keep `buyma_allowed_status=unchecked` until current BUYMA source rules are reviewed.
- Official/authentic status does not prove BUYMA sourcing permission.
- Gucci's personal/non-commercial sales restriction requires legal/operational review before resale purchasing.
- Never infer Japan shipping, VAT removal or durable stock from a displayed EU price.
- Validate every candidate's product status, size/color variant and checkout eligibility manually.

## Unresolved items

- Obtain written authorization or a documented partner/product-data agreement before automated collection.
- Recheck and archive `robots.txt` from an authorized environment.
- Verify raw-page canonical and JSON-LD fields manually without bypassing access controls.
- Confirm whether any official affiliate/feed program provides authorized product data.
- Review Gucci consumer-only purchase terms with counsel/operations for BUYMA resale sourcing.
- Review current BUYMA purchasing-source rules.
- Define periodic Terms, robots, VAT, shipping and category-policy rechecks.

## Official references

- [Gucci France FAQ](https://www.gucci.com/fr/fr/st/faq)
- [Gucci Germany FAQ](https://www.gucci.com/de/de/st/faq)
- [Gucci Italy FAQ](https://www.gucci.com/it/it/st/faq)
- [Gucci Spain FAQ](https://www.gucci.com/es/es/st/faq)
- [Gucci France legal and sales terms](https://www.gucci.com/fr/fr/st/legal-landing)
- [Gucci Germany legal and sales terms](https://www.gucci.com/de/de/st/legal-landing)
- [Gucci Italy legal and sales terms](https://www.gucci.com/it/it/st/legal-landing)
- [Gucci Spain legal and sales terms](https://www.gucci.com/es/es/st/legal-landing)
- [Representative France product page](https://www.gucci.com/fr/fr/pr/women/handbags/top-handle-bags-for-women/gucci-bamboo-1947-small-bag-p-863165AAGDM1096)
- [Representative Spain product page](https://www.gucci.com/es/es/pr/women/handbags/crossbody-bags-for-women/gucci-aperitivo-medium-shoulder-bag-p-866720FAFV29651)
- [Gucci robots.txt](https://www.gucci.com/robots.txt)
