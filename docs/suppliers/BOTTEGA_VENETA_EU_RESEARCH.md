# Bottega Veneta EU Official Supplier Research

Checked: 2026-08-15

## 1. Executive summary

Bottega Veneta operates localized EUR e-commerce storefronts for France, Germany, Italy and Spain. Official sales terms describe product codes, prices, color/size selection, checkout, pre-orders and personalized products. They also limit sales to consumers for personal, non-commercial purposes and allow suspected commercial orders to be refused. Each reviewed locale delivers only within its own country, not directly to Japan.

The conservative initial Supplier policy is `url_manual`, `automated_fetch_enabled=false`, `terms_status=restricted`, `robots_status=restricted`, `vat_policy=not_refunded` and `buyma_allowed_status=unchecked`. No documented public Product, inventory, price, affiliate API/feed or permission for automated collection was confirmed.

## 2. Country comparison

| Country | Official locale | Currency | Online purchase | EU locale to Japan | VAT evidence |
|---|---|---|---|---|---|
| France | `https://www.bottegaveneta.com/fr-fr/` | EUR | Confirmed; Add to cart and checkout are documented | No; delivery exclusively in France | Displayed prices include applicable VAT; no export deduction/refund confirmed |
| Germany | `https://www.bottegaveneta.com/de-de/` | EUR | Confirmed | No; delivery exclusively in Germany | Displayed prices include applicable VAT; no export treatment confirmed |
| Italy | `https://www.bottegaveneta.com/it-it/` | EUR | Confirmed | No; delivery only in Italy | Displayed prices include VAT; no export treatment confirmed |
| Spain | `https://www.bottegaveneta.com/es-es/` | EUR | Confirmed | No; delivery exclusively in Spain | Displayed prices include applicable VAT; no export treatment confirmed |

The locale-specific delivery restriction is also reflected in the FAQ: the delivery address must match the localized site. A separate Japanese locale is not evidence of EU-to-Japan shipping.

## 3. Global Category Master purchase matrix

| ProductCategory | Public-site evidence | Purchase classification |
|---|---|---|
| handbags | Dedicated catalog; product pages can expose Add to cart, pre-order, coming soon, or boutique discovery | Brand default; product restriction and availability dependent |
| small_leather_goods | Wallet, card-case and pouch catalogs with EUR prices | Brand default; product restriction and availability dependent |
| shoes | Women/men shoe catalogs with online order states | Brand default; product restriction and availability dependent |
| ready_to_wear | Women/men apparel catalogs with EUR prices | Brand default; product restriction and availability dependent |
| accessories | Belts, scarves, charms and other catalogs; personalization appears on individual items | Brand default; product restriction and availability dependent |
| jewelry | Jewelry catalog with EUR prices and mixed product states | Brand default; product restriction and availability dependent |
| watches | No stable official watch assortment was confirmed in this review | `unknown`; no override |
| eyewear | Sunglasses catalog with mixed normal/pre-order/boutique states | Brand default; product restriction and availability dependent |
| fragrance | Official FAQ includes fragrance support, but stable locale-wide purchase coverage was not confirmed | `unknown`; no override |
| beauty | A stable official beauty assortment was not confirmed | `unknown`; no override |

Catalog presence does not prove every product is purchasable. No stable category-wide rule differing from the Brand default was established, so no `BrandCategoryPolicy` seed is added.

## 4. Brand-level policy recommendation

Current Brand Master:

```text
brand_code=bottega_veneta
online_purchase_policy=unknown
is_research_enabled=true
```

Recommended: `limited`.

Broad official e-commerce is confirmed, so `boutique_only` or `research_only` would be inaccurate. `normal` is too permissive for sourcing: the sales terms restrict sales to personal, non-commercial consumers, commercial-looking orders may be refused, and individual products can be pre-order, personalized, coming soon or boutique-directed. This task does not modify Brand Master.

## 5. Product-level Purchase Restriction

Use the existing Product-level states only when the individual page provides evidence:

- `pre_order`: explicitly supported by the sales terms and visible on individual catalog entries.
- `personalized`: individual items may allow initials/personalization; personalized goods have special pricing/return conditions.
- `boutique_only`: use when an individual page only offers boutique discovery and no online order path.
- `client_advisor_only`: use only when the individual product requires a client advisor; a generic store-reservation service is insufficient.
- `made_to_order`: not confirmed; do not infer it from handcrafted production language.
- `research_only`: use only after a product-specific compliance/research decision.
- `normal`: use after a human confirms a current ordinary Add to cart flow.
- `unknown`: fail closed when evidence is missing or ambiguous.

The public review showed product-level differences within the same categories. These are not evidence for mechanical category overrides.

## 6. Availability separation

`sold out`, `out_of_stock`, `notify me`, `coming soon` and variant stock belong to `availability_status`. They do not become Product Purchase Restrictions. `pre_order` is different because it is a defined purchase path and remains `purchase_restriction=pre_order`. A boutique-only purchase route is a restriction even if boutique stock exists.

## 7. Product data available through normal public pages

Manual review can capture:

- localized product name and URL;
- product code/SKU where displayed or embedded in the product URL;
- EUR price and currency;
- color and size variants;
- product description, material, dimensions and care details where displayed;
- images;
- Add to cart, pre-order, coming-soon, boutique-discovery and personalization indicators;
- variant-level availability.

The official sales terms explicitly say product information, corresponding product codes and prices are available on the site. Values remain time-sensitive and require human confirmation.

## 8. Structured data

The limited normal-access review did not independently confirm a stable JSON-LD `Product`, schema.org `Offer`, SKU, `priceCurrency`, `availability`, variant or canonical contract across locales. A representative product page was visible through normal indexing, including name, EUR price, color and Add to cart, but this does not establish a supported structured-data interface.

Use `url_manual`, not `structured_data`. No raw-page probing, browser automation or access-control workaround was performed.

## 9. API and feed

No documented public Product, inventory, price, developer, affiliate or partner API/feed was found. Salesforce Commerce Cloud/Demandware browser routes are implementation details, not public APIs. The robots file restricts Demandware and commerce-helper routes.

```text
official_api_available=false
```

## 10. Terms of Use and Sales Terms

The four locale sales terms limit online sales to natural-person consumers purchasing for personal use outside trade/business/professional activity and not for profit. They allow orders to be refused for abnormal quantities or suspected commercial purposes. France, Germany and other reviewed localized terms also impose per-order quantity limits.

The France Terms of Use prohibit bypassing security measures, obtaining material not deliberately made available, and commercial/professional use or reproduction of site content without written permission. No express permission for automated extraction, commercial data reuse or resale sourcing was confirmed. `terms_status=restricted` is a conservative system classification, not legal advice.

## 11. robots.txt

`https://www.bottegaveneta.com/robots.txt` was retrieved once. It publishes locale sitemaps but restricts account/cart/login, Demandware host/routes, search and product helper/variation routes and parameterized catalog paths.

Set `robots_status=restricted`. A crawlable public product URL is not contractual authorization for automated or commercial collection.

## 12. Shipping

The official terms say purchased goods are delivered exclusively within France, Germany, Italy or Spain for their respective storefronts. Freight-forwarder addresses are also excluded. Set `ships_to_japan=false`; do not infer a forwarding workaround.

## 13. VAT

Displayed prices include the applicable VAT/sales taxes. No official evidence reviewed here establishes an export price, checkout VAT deduction, tax-free sale or VAT refund for an EU-localized order shipped domestically. Use:

```text
vat_policy=not_refunded
vat_rate=null
```

The null rate avoids treating a statutory national rate as a confirmed supplier checkout/refund policy.

## 14. Recommended Supplier Policy

Apply to all four locale Suppliers:

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

`authorized_retailer` is the closest existing Supplier type for a brand-operated official store; it does not assert BUYMA approval.

## 15. Ingestion recommendation

Only operator-entered public product URLs should be recorded. Do not enable a parser, structured-data ingestion, headless browser, internal endpoint, session scraping or scheduled fetching. Manual review must record the current price, variant, availability, Product Purchase Restriction and evidence timestamp.

## 16. BUYMA considerations

Keep `buyma_allowed_status=unchecked`. Before any listing, an operator must confirm current BUYMA sourcing rules, whether the specific shop/receipt is acceptable, authenticity documentation, personal/non-commercial purchase restrictions, forwarding restrictions, quantity limits, VAT assumptions, return limitations for personalized goods and current product availability. Official-store status alone is insufficient.

## 17. Comparison with existing research

| Brand | Brand default assessment | Category override | EU to Japan | Automated ingestion |
|---|---|---|---|---|
| Hermès | Conservative/research-oriented | Category differences can be material | Not established | Disabled |
| CHANEL | Category-limited | Material category differences | Not established | Disabled |
| Gucci | Limited | No evidenced seed requirement | Not established | Disabled |
| Prada | Limited | No evidenced seed requirement | No | Disabled |
| Saint Laurent | Limited | No evidenced seed requirement | No | Disabled |
| Bottega Veneta | Recommend `limited` | No evidenced seed requirement | No | Disabled |

Bottega Veneta most closely resembles Prada and Saint Laurent: broad official e-commerce, consumer/non-commercial restrictions, domestic locale delivery, and important product-level states.

## 18. Unresolved items

- Legal/operator review of commercial resale and BUYMA compatibility.
- Current BUYMA prohibited/caution sourcing status and receipt requirements.
- Per-product canonical and JSON-LD markup stability.
- Watches, fragrance and beauty category coverage by locale.
- VAT refund/tax-free eligibility for any separately approved purchase method.
- Current variant stock, pre-order, personalization and boutique-only states.
- Any future official affiliate/partner feed offered under contract.

## 19. Sources

- France sales terms: https://www.bottegaveneta.com/fr-fr/mentions-legales/terms-and-conditions-sale.html
- Germany sales terms: https://www.bottegaveneta.com/de-de/legal-pages/terms-and-conditions-sale.html
- Italy sales terms: https://www.bottegaveneta.com/it-it/menzioni-legali/terms-and-conditions-sale.html
- Spain legal notice and sales terms: https://www.bottegaveneta.com/es-es/terminos-legales/legal-notice.html
- Germany FAQ: https://www.bottegaveneta.com/de-de/faq
- robots: https://www.bottegaveneta.com/robots.txt
- Representative France product page: https://www.bottegaveneta.com/fr-fr/sac-tote-amaranto-592122VMBK16215.html
- Germany ready-to-wear catalog: https://www.bottegaveneta.com/de-de/damen/damenbekleidung/tops-und-t-shirts
- Germany handbags catalog: https://www.bottegaveneta.com/de-de/damen/taschen/schultertaschen
- Germany jewelry catalog: https://www.bottegaveneta.com/de-de/geschenke/herren-geschenke/schmuck
- Germany eyewear catalog: https://www.bottegaveneta.com/de-de/damen/damenbrillen/sonnenbrillen/intrecciato

Sources were checked with minimal normal public access. No CAPTCHA, anti-bot or access-control bypass, browser automation, login, proxy rotation, internal endpoint use or bulk request was used.
