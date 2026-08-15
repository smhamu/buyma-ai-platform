# Prada EU Official Online Supplier Research

Checked: 2026-08-15

## 1. Executive Summary

Prada operates localized official e-commerce sites for France, Germany, Italy and Spain. Product listings and detail pages expose EUR prices and broad online purchase functionality across fashion, bags, small leather goods, shoes, accessories, jewelry, eyewear, beauty and fragrance. Availability remains product/variant-specific; pre-order, personalized, coming-soon and notify-me states exist.

The country sales terms reserve purchasing to consumers and expressly prohibit resale or transfer for commercial/professional purposes. No automated collection permission or documented public Product API was found. Initial Supplier records must therefore use `url_manual`, `automated_fetch_enabled=false`, `terms_status=restricted` and `buyma_allowed_status=unchecked`.

## 2. Country Comparison

| Country | Official URL / locale | Currency | Online purchase | EU locale to Japan | VAT evidence | Sales restriction |
|---|---|---|---|---|---|---|
| France | `https://www.prada.com/fr/fr/` | EUR | Yes | No; France delivery address required | Included; online refund unavailable | Commercial resale expressly prohibited |
| Germany | `https://www.prada.com/de/de/` | EUR | Yes | No; Germany delivery address required | Included; no export deduction confirmed | Commercial resale expressly prohibited |
| Italy | `https://www.prada.com/it/it/` | EUR | Yes | No; listed delivery territories exclude Japan | Included; no online refund evidence supporting deduction | Commercial resale expressly prohibited |
| Spain | `https://www.prada.com/es/es/` | EUR | Yes | No; territory/point-of-sale delivery restrictions | Included; online refund unavailable | Commercial resale expressly prohibited |

The existence of Prada Japan is not evidence that an EU storefront ships to Japan. `ships_to_japan=false` reflects these EU locale contracts only.

## 3. Brand-level Policy Recommendation

Brand Master currently stores Prada as `online_purchase_policy=unknown`. The closest existing value is `limited`: online purchase is broad, but product availability varies and the official sales terms prohibit commercial resale. This task does not update Brand Master.

`normal` would obscure a material sourcing restriction; `category_limited`, `boutique_only` and `research_only` do not match the broad observable e-commerce catalog.

## 4. Category Purchase Matrix

| ProductCategory | Listing/detail and EUR price | Purchase observation | Policy conclusion |
|---|---|---|---|
| handbags | Confirmed | Add to Bag, personalization, stock states | Brand default sufficient |
| small_leather_goods | Confirmed through accessories catalog | Online purchase is broadly represented | Brand default sufficient |
| shoes | Confirmed | Prices and online-exclusive/pre-release examples | Brand default sufficient |
| ready_to_wear | Confirmed | Prices, sizes and online-exclusive examples | Brand default sufficient |
| accessories | Confirmed | Multiple purchasable subcategories | Brand default sufficient |
| jewelry | Confirmed | EUR-priced catalog, pre-order/coming soon states | Brand default sufficient |
| watches | Relevant Prada category not sufficiently confirmed in the reviewed EU catalog | Do not infer boutique or online behavior | Unresolved; no override |
| eyewear | Confirmed | EUR-priced catalog and virtual try-on | Brand default sufficient |
| fragrance | Confirmed | EUR-priced products/listings | Brand default sufficient |
| beauty | Confirmed | Official Beauty & Fragrances catalog | Brand default sufficient |

Page existence, price display and purchasability are recorded separately. Product-level `sold out`, `pre-order`, `personalized`, `coming soon`, size/color availability and inquiry states are not Category Policy.

## 5. Category Override Recommendation

No Prada Category Policy seed is warranted. The confirmed categories are consistent with the proposed `limited` Brand default, and evidence for Watches is insufficient. Creating an override for every online category would duplicate the fallback and weaken the evidence model.

## 6. Product Data Availability

Representative official pages expose:

- product name and locale URL
- product code embedded in the URL and displayed as `Product code`
- EUR price
- availability/add-to-bag or notify-me state
- color, material, dimensions and size
- multiple images
- personalization where supported
- variants represented by code/color/size selections

The URL appears stable for manual evidence. Canonical link markup was not independently verified.

## 7. Structured Data

Publicly indexed content confirms human-visible product data, but does not establish stable `schema.org/Product`, `Offer`, SKU, price, priceCurrency, availability or canonical markup. No repeated raw-page probing or access-control bypass was performed. JSON-LD remains unconfirmed and `structured_data` is not recommended.

Even verified JSON-LD would not provide legal authorization for automated commercial reuse.

## 8. API

No documented third-party public Product API, developer API, supported public GraphQL endpoint, affiliate feed or partner product feed was found. Browser-internal endpoints are not public APIs.

Set `official_api_available=false`.

## 9. Terms

All reviewed country sales terms reserve distance sales to consumers acting outside commercial/professional activity. France, Germany, Italy and Spain explicitly prohibit resale or transfer of purchased products for commercial or professional purposes. Italy also identifies suspected resale as a reason to reject an order.

No explicit permission for automated product-data collection, extraction, scraping or crawling was found. Site content and use restrictions require separate legal review. Set `terms_status=restricted`; this is not softened by robots rules.

## 10. robots

`https://www.prada.com/robots.txt` was retrieved once on 2026-08-15. It provides public sitemaps but disallows content repositories, search, account/profile/order routes and an internal person JSON route. Product/category URLs are not globally disallowed; API/stock/cart patterns are not comprehensively enumerated.

Set `robots_status=restricted`. This reflects mixed route rules, not permission to automate. Search, account, checkout and internal content routes must never be used for ingestion.

## 11. Shipping

France and Germany sales terms require domestic delivery addresses. Italy lists a limited group of delivery territories, excluding Japan. Spain limits delivery according to the responsible country/store structure and asks customers to verify other territories. None establishes direct EU-locale shipping to a Japanese residential address.

Set `ships_to_japan=false`; do not infer cross-region delivery from the existence of a Japanese storefront or from generic “worldwide e-store countries” FAQ language.

## 12. VAT

All four sales terms state that displayed prices include VAT. France and Spain FAQs explicitly state that VAT refunds are unavailable for online purchases. No official evidence establishes automatic VAT removal for direct export or forwarding orders.

```text
vat_policy=not_refunded
vat_rate=null
```

VAT-inclusive does not imply export-price deduction. No VAT amount is automatically removed from profit calculations.

## 13. BUYMA Considerations

- Keep `buyma_allowed_status=unchecked`; an official site is not automatically an allowed BUYMA sourcing channel.
- The explicit commercial-resale prohibition is a material operational/legal issue.
- Do not use EU list prices as export-net prices.
- Verify checkout eligibility and product variant stock manually for every candidate.
- Do not confuse an EU site with Prada Japan or assume forwarding is permitted.

## 14. Recommended Supplier Policy

```text
supplier_type=authorized_retailer
country_code=FR / DE / IT / ES
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
robots_status=restricted
official_api_available=false
parser_key=null
request_interval_seconds=null
```

## 15. Comparison with Hermès / CHANEL / Gucci

This table uses only the existing research documents and this review.

| Dimension | Hermès | CHANEL | Gucci | Prada |
|---|---|---|---|---|
| General online purchase | Conservative/research-led | Category-limited | Broad, product-dependent | Broad, product-dependent |
| Category restrictions | Brand default retained | Major Fashion vs Beauty split | No justified override | No justified override |
| Product-level restrictions | Candidate verification required | Category and product checks | Sold out/pre-order/personalized/advisor | Stock/pre-order/personalized/coming soon |
| Japan direct shipping | EU Supplier false | EU Supplier false | EU Supplier false | EU Supplier false |
| VAT | Not refunded policy | IT included; others unknown in prior review | Not refunded | Not refunded |
| Structured data | Not selected | Unconfirmed | Unconfirmed | Unconfirmed |
| Public API | None confirmed | None confirmed | None confirmed | None confirmed |
| Terms | Restricted | Restricted | Restricted | Restricted; resale expressly prohibited |
| robots | Allowed at review date | Restricted | Unknown | Restricted |
| Recommended ingestion | `url_manual` | `url_manual` | `url_manual` | `url_manual` |

## 16. Unresolved Items

- Obtain legal/operations guidance on Prada's express commercial-resale prohibition before sourcing.
- Review current BUYMA purchasing-source rules.
- Confirm Watches behavior without inferring from other categories.
- Verify canonical and JSON-LD markup manually without bypasses.
- Ask Prada whether an authorized product feed or data-use agreement exists.
- Recheck Terms, robots, VAT and delivery evidence periodically.
- Product-level availability/restriction domain remains separate future work.

## 17. Sources / Checked Date

Checked 2026-08-15:

- [Prada France sales terms](https://www.prada.com/fr/fr/info/terms-conditions.html)
- [Prada Germany sales terms](https://www.prada.com/de/de/info/terms-conditions.html)
- [Prada Italy sales terms](https://www.prada.com/it/it/info/terms-conditions.html)
- [Prada Spain sales terms](https://www.prada.com/es/es/info/terms-conditions.html)
- [Prada France shipping FAQ](https://www.prada.com/fr/fr/info/faqs/shipments.html)
- [Prada France tax refund FAQ](https://www.prada.com/fr/fr/info/faqs/tax-refund.html)
- [Prada Spain tax refund FAQ](https://www.prada.com/es/es/info/faqs/tax-refund.html)
- [Representative Spain product page](https://www.prada.com/es/es/p/bolso-de-piel-pequeno/1BC145_2DKV_F0632_V_7NM)
- [Prada Spain jewelry catalog](https://www.prada.com/es/es/womens/accessories/jewels/c/10621EU)
- [Prada Spain Beauty catalog](https://www.prada.com/es/es/beauty-and-fragrances/beauty/c/10565EU/page/-1)
- [Prada robots.txt](https://www.prada.com/robots.txt)
