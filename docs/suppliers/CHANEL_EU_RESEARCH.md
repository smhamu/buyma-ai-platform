# CHANEL EU Official Online Supplier Research

Research date: 2026-08-15

## Summary

France, Germany, Italy and Spain use country paths on `www.chanel.com`. CHANEL offers online sales only for selected categories. Fragrance, Makeup, Skincare and Sunglasses are explicitly included in the Online Boutique. Fashion products such as bags, small leather goods and shoes remain primarily boutique-led. A limited selection of Watches and Jewelry may support Click & Collect in some markets.

All four Supplier records should start with `ingestion_source_type=url_manual` and `automated_fetch_enabled=false`. Direct requests to four representative product pages returned HTTP 403. No attempt was made to bypass the refusal. JSON-LD and raw HTML fields therefore remain unconfirmed in this review.

## Country comparison

| Country | Official URL | EUR prices | Online purchase | Japan delivery | VAT evidence | Recommended source |
|---|---|---|---|---|---|---|
| France | `https://www.chanel.com/fr/` | Yes | Category-limited | Not listed | Tax treatment not confirmed sufficiently | `url_manual` |
| Germany | `https://www.chanel.com/de/` | Yes | Category-limited | Not listed | Tax treatment not confirmed sufficiently | `url_manual` |
| Italy | `https://www.chanel.com/it/` | Yes | Category-limited | Not listed | Online prices stated as tax-inclusive | `url_manual` |
| Spain | `https://www.chanel.com/es/` | Yes | Category-limited | Not listed | Tax treatment not confirmed sufficiently | `url_manual` |

The Fragrance & Beauty delivery list includes multiple European countries but not Japan. This is not evidence that every category can be delivered to every listed country. Supplier Master therefore uses `ships_to_japan=false`.

## Online purchase restrictions

The Brand Master currently sets CHANEL to `online_purchase_policy=research_only`. That remains appropriate because one brand-level value cannot safely represent the category differences below.

| Category | Observed purchase mode | Policy interpretation |
|---|---|---|
| Fashion | Product discovery and boutique/contact flow | `boutique_only` / `research_only` |
| Bags | Fashion boutique flow; no general EU home-delivery offer confirmed | `boutique_only` |
| Small leather goods | Fashion boutique flow; no general EU home-delivery offer confirmed | `boutique_only` |
| Shoes | Fashion boutique flow; no general EU home-delivery offer confirmed | `boutique_only` |
| Jewelry | Boutique-led; selected France items may use Click & Collect | `category_limited` |
| Watches | Boutique/authorized retailer-led; selected France items may use Click & Collect | `category_limited` |
| Eyewear | Explicitly included in the Online Boutique | `normal` for eligible products/markets |
| Fragrance | Explicitly included in the Online Boutique | `normal` for eligible products/markets |
| Beauty / Makeup / Skincare | Explicitly included in the Online Boutique | `normal` for eligible products/markets |

Online status must be evaluated per candidate and category. It must not be inferred solely from the Supplier being active.

## Product data availability

Official indexed pages expose product names, reference numbers such as `116260`, EUR prices and add-to-cart wording for eligible Fragrance/Beauty products. Fashion, Watch and Jewelry pages expose descriptions, references, colors, materials, sizes or prices depending on category, but those fields do not prove home-delivery availability.

The following raw-page fields were not confirmed because all four representative direct product requests returned HTTP 403:

- canonical URL markup
- JSON-LD Product
- machine-readable SKU
- machine-readable price/currency
- machine-readable availability
- variant/color/size data structures

The refusal was not bypassed and no headless browser, login, proxy or anti-bot technique was used.

## JSON-LD

Unconfirmed for all four locales in this review. Search results showing product data are not sufficient evidence that `application/ld+json` is present. `structured_data` must not be selected without a permitted, repeatable verification and Terms approval.

## Official / public Product API

No documented public Product, price or stock API was found. Browser-internal endpoints are not treated as public APIs. The robots file explicitly disallows `*/api/*`, `/*.json`, `*/loadVariant/*` and `*/stock/*`.

Set `official_api_available=false`.

## Terms

The France, Germany, Italy and Spain legal pages describe the site, databases, software, product content, images and other elements as protected CHANEL intellectual property. No explicit authorization for automated commercial product collection was found.

Set `terms_status=restricted`. Written permission or a documented partner/public API agreement is required before reconsidering automated collection.

## robots.txt

`https://www.chanel.com/robots.txt` was requested once on 2026-08-15.

Relevant rules include:

- `Disallow: /*.json`
- `Disallow: */api/*`
- `Disallow: */yapi/*`
- `Disallow: */loadVariant/*`
- `Disallow: */stock/*`
- search, cart, checkout, wishlist and account paths are disallowed
- public product page paths are not globally disallowed

Because data/API/variant/stock routes relevant to ingestion are explicitly restricted, set `robots_status=restricted`. This robots result does not independently determine legal permission.

## VAT

Italy's current online sales terms state that prices are shown in EUR including taxes, so the Italy seed uses `vat_policy=included`. This does not mean VAT can be deducted or refunded for export.

The reviewed France, Germany and Spain material was insufficient to safely establish an export deduction or refund rule, so those seeds use `vat_policy=unknown`. All seeds use `vat_rate=null`; no automatic VAT removal is permitted.

## Shipping

The official Fragrance & Beauty FAQ lists supported European delivery countries. Japan is not included. Fashion, Watches and Jewelry have separate boutique or Click & Collect restrictions. All four EU locale Suppliers use `ships_to_japan=false`.

## Recommended Supplier Policy

```text
supplier_type=authorized_retailer
default_currency=EUR
ships_to_japan=false
vat_policy=unknown (FR/DE/ES), included (IT)
vat_rate=null
buyma_allowed_status=unchecked
research_status=reviewing
ingestion_source_type=url_manual
automated_fetch_enabled=false
terms_status=restricted
robots_status=restricted
official_api_available=false
parser_key=null
request_interval_seconds=null
```

The presence of an official CHANEL site does not by itself prove that the source is permitted under current BUYMA purchasing rules.

## Seed

`backend/scripts/seed_chanel_eu_suppliers.py` asks for an active Admin owner and links four country Suppliers to the global `chanel` Brand.

```bash
cd backend
python scripts/seed_luxury_brands.py
python scripts/seed_chanel_eu_suppliers.py
```

The seed is idempotent by owner and Supplier name. Existing Supplier records are neither updated nor overwritten. A missing CHANEL Brand causes a fail-closed error.

## BUYMA considerations

- Keep `buyma_allowed_status=unchecked` until the current BUYMA purchasing-source rules are reviewed.
- Do not treat displayed Fashion prices as proof of online purchasability.
- Check category, country, delivery method and stock for every candidate.
- Do not assume Click & Collect inventory can be shipped to Japan.
- Do not infer VAT refund eligibility from an inclusive displayed price.

## Unresolved items

- Obtain written clarification from CHANEL regarding product-data use or an official API.
- Verify JSON-LD and canonical markup manually in a normal browser without automation.
- Confirm current VAT/export treatment separately for France, Germany and Spain.
- Confirm category-specific purchase and Click & Collect support in each country.
- Review current BUYMA purchasing-source rules.
- Schedule periodic Terms and robots rechecks.

## Official references

- [CHANEL France legal and terms](https://www.chanel.com/fr/mentions-legales/)
- [CHANEL Germany legal and terms](https://www.chanel.com/de/rechtliche-hinweise/)
- [CHANEL Italy legal and terms](https://www.chanel.com/it/menzioni-legali/)
- [CHANEL Spain legal and terms](https://www.chanel.com/es/notas-legales/)
- [CHANEL Italy online sales terms](https://services.chanel.com/i18n/it_IT/pdf/cgv_it_IT.pdf)
- [CHANEL France Fragrance & Beauty FAQ](https://www.chanel.com/fr/faq/parfums-beaute/)
- [CHANEL Italy Fragrance & Beauty FAQ](https://www.chanel.com/it/faq/fragrance-beauty/)
- [CHANEL Spain Fragrance & Beauty FAQ](https://www.chanel.com/es/faq/fragrance-beauty/)
- [CHANEL France Jewelry FAQ](https://www.chanel.com/fr/faq/joaillerie/)
- [CHANEL France Watches FAQ](https://www.chanel.com/fr/faq/horlogerie/)
- [CHANEL Spain Fashion FAQ](https://www.chanel.com/es/faq/moda/)
- [CHANEL robots.txt](https://www.chanel.com/robots.txt)
