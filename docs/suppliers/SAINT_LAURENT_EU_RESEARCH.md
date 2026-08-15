# Saint Laurent / YSL EU Official Supplier Research

Checked: 2026-08-15

## 1. Executive summary

Saint Laurent operates localized EUR e-commerce storefronts for France, Germany, Italy and Spain. The official sales terms describe product codes, prices, color/size selection, Add to Bag and product-specific pre-orders. They also limit sales to consumers for personal, non-commercial purposes and permit rejection of suspected commercial purchases. Each reviewed locale delivers only within its own country, so an EU storefront must not be treated as shipping directly to Japan.

The safe initial Supplier policy is `url_manual`, `automated_fetch_enabled=false`, `terms_status=restricted`, `robots_status=restricted` and `buyma_allowed_status=unchecked`. No documented public Product API or permission for automated collection was confirmed.

## 2. Country comparison

| Country | Official locale | Currency | Online purchase | EU locale to Japan | VAT evidence |
|---|---|---|---|---|---|
| France | `https://www.ysl.com/fr-fr/` | EUR | Confirmed; terms describe Add to Bag and checkout | No; delivery exclusively in France | Displayed prices include VAT; no export deduction/refund confirmed |
| Germany | `https://www.ysl.com/de-de/` | EUR | Confirmed | No; delivery exclusively in Germany | Applicable VAT included in amount payable; no export treatment confirmed |
| Italy | `https://www.ysl.com/it-it/` | EUR | Confirmed | No; delivery only in Italy | Applicable VAT included; no export treatment confirmed |
| Spain | `https://www.ysl.com/es-es/` | EUR | Confirmed | No; delivery exclusively in Spain | Applicable VAT included; no export treatment confirmed |

The Japanese YSL storefront is separate evidence and does not establish cross-region shipping from an EU locale.

## 3. Category purchase matrix

| ProductCategory | Official-site evidence | Purchase classification |
|---|---|---|
| handbags | Dedicated catalog and normal online order flow | Brand default; availability/product restriction dependent |
| small_leather_goods | Dedicated wallet/card-case catalog | Brand default; availability/product restriction dependent |
| shoes | Dedicated women/men catalog | Brand default; availability/product restriction dependent |
| ready_to_wear | Dedicated women/men catalog | Brand default; availability/product restriction dependent |
| accessories | Belts, scarves, hats and other online catalog entries | Brand default; availability/product restriction dependent |
| jewelry | Costume/fine-jewelry catalog entries | Brand default; availability/product restriction dependent |
| watches | No actual watch category was confirmed; a “watches box” product is not evidence of watches | Unknown; no override |
| eyewear | Sunglasses are included under accessories | Brand default; availability/product restriction dependent |
| fragrance | Official fragrance catalog is linked from Gifts | Brand default where a locale offers Add to Bag; product evidence required |
| beauty | A general Saint Laurent fashion-store beauty category was not confirmed; do not conflate external YSL Beauty distribution | Unknown; no override |

Catalog presence does not prove that every item is purchasable. No category-wide boutique-only or client-advisor-only rule was established.

## 4. Brand Policy recommendation

Current Brand Master:

```text
brand_code=saint_laurent
online_purchase_policy=unknown
is_research_enabled=true
```

Recommended: `limited`.

Reason: broad official e-commerce is confirmed, so `boutique_only` and `research_only` misdescribe product access. `normal` is too permissive for BUYMA sourcing because the sales terms limit purchases to personal/non-commercial consumers and permit refusal of suspected commercial purchases. This document does not modify Brand Master.

## 5. Category Policy recommendation

No `BrandCategoryPolicy` seed is justified. Confirmed online categories follow the same Brand default, while watches and beauty lack enough evidence. Duplicate overrides would not add evidence. A future override should require an explicit, stable category-wide rule.

## 6. Product-level restriction findings

- Official country terms explicitly provide for selected `pre_order` products. Record this on the individual source/candidate as `purchase_restriction=pre_order`.
- The terms describe extra services and non-returnability for personalized products. Record verified individual products as `personalized`.
- `client_advisor_only`, `boutique_only` and `made_to_order` were not established as general rules; use them only when an individual page supplies evidence.
- A normal Add to Bag product may be `normal`, but only after a human verifies the current page.
- Missing or ambiguous evidence remains `unknown` and fails closed for Ready for Listing.

Product restrictions do not override a restrictive Brand or Category Policy.

## 7. Availability findings

Availability is variant-specific and can change between selection and checkout. `in_stock`, `out_of_stock`, `sold out`, and `notify me/notify when available` belong to `availability_status`, not `ProductPurchaseRestriction`. A pre-order is different: it is an order path for a selected product and belongs to `purchase_restriction=pre_order`.

## 8. Product data

The sales terms and normally indexed product/category pages support manual capture of:

- name and locale-specific URL;
- product code/SKU where displayed or encoded in the product URL;
- EUR price and currency;
- color, size and quantity selection;
- descriptions, materials and, where supplied, dimensions;
- product images;
- variant-level availability and Add to Bag/pre-order state.

Canonical markup and stable variant identifiers were not independently verified. Product data remains evidence to review, not a promise of purchase availability.

## 9. Structured data

Stable JSON-LD `Product`, schema.org `Offer`, `priceCurrency`, `availability`, SKU and canonical markup were not confirmed through the limited normal-access review. No additional raw-page probing or browser automation was performed. `structured_data` is therefore not recommended.

## 10. API

No documented public Product, inventory, price, developer, affiliate or partner API was found. Salesforce Commerce Cloud/Demandware routes and browser-internal endpoints are not public APIs; robots explicitly disallows `/api/data/*`, `/api/v1/*` and `/on/demandware*` paths.

```text
official_api_available=false
```

## 11. Terms

All four sales terms limit online sales to natural-person consumers purchasing for personal consumption outside trade, business, craft or profession and not for profit. They permit rejecting abnormal quantities or purchases suspected to be for commercial purposes. This is a material sourcing risk even though the catalog is publicly viewable.

The reviewed Terms of Use prohibit bypassing security measures and attempting to obtain information not deliberately made available. No explicit permission for automated product extraction, commercial database reuse or scraping was confirmed. `terms_status=restricted` is a conservative system policy, not a legal conclusion.

## 12. robots

`https://www.ysl.com/robots.txt` was retrieved once. It publishes locale sitemaps but disallows account/cart, Demandware, product-variation, product size/zoom helpers, search/AJAX, `/api/data/*`, `/api/v1/*` and numerous parameterized routes.

Set `robots_status=restricted`. Public product pages not being globally disallowed does not grant contractual permission to automate.

## 13. Shipping

France, Germany, Italy and Spain terms each state that delivery is exclusive to that country. They also reject freight-forwarder addresses. Set `ships_to_japan=false`. A human must validate any lawful sourcing/forwarding arrangement separately; the application must not infer it.

## 14. VAT

Displayed/paid prices include applicable VAT. No reviewed official evidence establishes export-price deduction, destination-based VAT removal or online VAT refund for these domestic storefront orders. Use:

```text
vat_policy=not_refunded
vat_rate=null
```

The null rate avoids deriving a contractual treatment from general national VAT rates.

## 15. Recommended Supplier Policy

Applies to all four locale Suppliers:

```text
supplier_type=authorized_retailer
default_currency=EUR
ships_to_japan=false
vat_policy=not_refunded
vat_rate=null
buyma_allowed_status=unchecked
research_status=reviewing
is_active=true
ingestion_source_type=url_manual
automated_fetch_enabled=false
terms_status=restricted
robots_status=restricted
official_api_available=false
parser_key=null
request_interval_seconds=null
```

`authorized_retailer` is the closest existing Supplier type for a brand-operated official store; it does not imply BUYMA approval.

## 16. Ingestion recommendation

Use manual URL evidence only. Do not use CSV as an automated feed, structured-data extraction, a supplier parser, browser endpoints or API routes. Product code, price, restriction and availability require current human confirmation.

## 17. BUYMA considerations

Keep `buyma_allowed_status=unchecked`. Official-store status alone does not establish BUYMA acceptability, and the Saint Laurent consumer/non-commercial purchase terms create a separate resale risk. A human must confirm current BUYMA sourcing rules, order purpose, destination, VAT assumptions and product availability before listing.

## 18. Cross-brand comparison

| Brand | Brand default assessment | Category override | Product restriction importance | EU→Japan | Automated ingestion |
|---|---|---|---|---|---|
| Hermès | Research-oriented/conservative | Category differences material | High | Not established | Disabled |
| CHANEL | Category-limited | Material due category-specific e-commerce | High | Not established | Disabled |
| Gucci | Limited | No evidenced seed requirement in current research | High | Not established | Disabled |
| Prada | Limited | No evidenced seed requirement | High | No | Disabled |
| Saint Laurent | Recommend `limited` | No evidenced seed requirement | High: pre-order/personalized are explicit | No | Disabled |

Saint Laurent resembles Prada in broad e-commerce plus consumer/commercial-purpose restrictions. It differs from CHANEL, where category-level online availability is more central. Product-level review remains essential across all brands.

## 19. Unresolved items

- Human/legal review of commercial resale and BUYMA sourcing compatibility.
- Whether any product-category-wide boutique/client-advisor constraint later emerges.
- Watches and fashion-store beauty category coverage.
- Per-product canonical and JSON-LD markup.
- VAT refund/tax-free eligibility for any permitted purchase method.
- Current variant stock, pre-order and personalization states.
- Any future official affiliate/partner feed made available under contract.

## 20. Sources

- France sales terms: https://www.ysl.com/fr-fr/legal/terms-and-conditions-of-sale
- Germany sales terms: https://www.ysl.com/de-de/legal/terms-and-conditions-of-sale
- Italy sales terms: https://www.ysl.com/it-it/legal/terms-and-conditions-of-sale
- Spain sales terms: https://www.ysl.com/es-es/legal/terms-and-conditions-of-sale
- France Terms of Use: https://www.ysl.com/fr-fr/legal/terms-and-conditions-of-use
- robots: https://www.ysl.com/robots.txt
- France handbags catalog: https://www.ysl.com/en-fr/ca/shop-women/handbags
- France ready-to-wear catalog: https://www.ysl.com/en-fr/ca/shop-women/ready-to-wear
- Spain fragrance catalog: https://www.ysl.com/en-es/ca/new-arrivals/gifts/fragrances

Sources were checked with minimal normal public access. No access controls were bypassed and no browser automation, proxy rotation, internal API use or bulk requests were used.
