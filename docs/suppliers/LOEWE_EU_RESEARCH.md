# LOEWE EU Official Supplier Research

Checked: 2026-08-15

## 1. Executive Summary

LOEWE operates a European storefront with French, German, Italian and Spanish language routes and EUR pricing. Broad online purchasing is available, including fashion, leather goods, eyewear and fragrance. Official terms state that orders are for personal use or gifts, prohibit resale and commercial activity, and permit cancellation when commercial activity is indicated.

The global shipping table includes Japan, but LOEWE requires the shopper to select a destination country/region so that the correct currency, payment methods and shipping conditions apply. This is not evidence that an EU/EUR locale order can be shipped directly to Japan. The conservative EU Supplier policy is therefore `ships_to_japan=false`, `url_manual`, `automated_fetch_enabled=false`, `terms_status=restricted`, `robots_status=restricted` and `buyma_allowed_status=unchecked`.

## 2. Country Comparison

| Country | Official language/region URL | Currency | Online purchase | EU/EUR checkout to Japan | VAT |
|---|---|---|---|---|---|
| France | `https://www.loewe.com/eur/fr/` | EUR | Confirmed; Add to cart and checkout documented | Not confirmed; destination selection controls checkout and France terms describe domestic delivery | Prices include VAT; no export deduction/refund confirmed |
| Germany | `https://www.loewe.com/eur/de/` | EUR | Confirmed | Not confirmed; Japan is a separate destination/region selection | Prices include applicable taxes; no EU-export treatment confirmed |
| Italy | `https://www.loewe.com/eur/it/` | EUR | Confirmed | Not confirmed; Japan is a separate destination/region selection | Prices include applicable taxes; no EU-export treatment confirmed |
| Spain | `https://www.loewe.com/eur/es/` | EUR | Confirmed | Not confirmed; Japan is a separate destination/region selection | Prices include applicable taxes; no EU-export treatment confirmed |

These URLs are European language routes, not proof of four independent stock pools. Country-specific payment, delivery and return conditions must be checked at order time.

## 3. Brand Policy Recommendation

Current Brand Master:

```text
brand_code=loewe
online_purchase_policy=unknown
is_research_enabled=true
```

Recommended: `limited`.

Broad e-commerce makes `boutique_only` and `research_only` inaccurate. `normal` is too permissive for BUYMA sourcing because resale is expressly prohibited, commercial-looking orders may be cancelled, and individual products can be pre-order or personalized. Brand Master is not changed by this task.

## 4. Category Purchase Matrix

| ProductCategory | Listing/detail and EUR price | Purchase evidence | Classification |
|---|---|---|---|
| handbags | Confirmed | Broad online catalog; individual variants require review | Brand default |
| small_leather_goods | Confirmed | Wallet and card-holder catalog entries | Brand default |
| shoes | Confirmed | Women/men shoe catalog entries | Brand default |
| ready_to_wear | Confirmed | Women/men collections with EUR prices | Brand default |
| accessories | Confirmed | Belts, scarves, charms and personalization accessories | Brand default; product restriction dependent |
| jewelry | Confirmed | Jewelry entries under accessories | Brand default |
| watches | Not confirmed | No stable official watch assortment found | `unknown`; no override |
| eyewear | Confirmed | Sunglasses listings with EUR prices | Brand default |
| fragrance | Confirmed | Women/men fragrance catalogs and EUR prices | Brand default; hygiene/return rules apply |
| beauty | Not confirmed | Fragrance must not be generalized to a beauty category | `unknown`; no override |

A listing or price is not proof of current Add to Bag availability. Product and variant evidence remains necessary.

## 5. Category Policy Recommendation

No `BrandCategoryPolicy` seed is justified. Confirmed categories follow the same Brand default, while watches and beauty lack sufficient evidence. Fragrance-specific return conditions do not constitute a purchase-policy override. Product-specific pre-order and personalization must remain Product-level restrictions.

## 6. Product-level Restrictions

- `normal`: current ordinary Add to Bag flow confirmed by a human.
- `pre_order`: official terms explicitly identify special pre-order collections.
- `personalized`: personalization is offered on selected leather goods/bags; personalized products are non-returnable.
- `made_to_order`: not independently confirmed; customer specifications in return-law text are not sufficient evidence.
- `client_advisor_only`: not established as a general route; use only on explicit individual evidence.
- `boutique_only`: use where an individual page offers reservation/store service without online purchase.
- `research_only`: operator compliance decision for an individual candidate.
- `unknown`: missing or ambiguous evidence; fail closed.

Do not promote product-specific restrictions into Category Policy.

## 7. Availability Findings

`in_stock`, `out_of_stock`, `sold out`, `notify me` and `coming soon` belong to `availability_status`. Official catalog filters expose “In stock,” and terms acknowledge changing stock. These states are independent of Product Purchase Restriction. A pre-order may be purchasable while not currently in ordinary stock.

## 8. Product Data

Normal public pages support manual capture of:

- localized product name and URL;
- product/reference code when displayed;
- EUR price and currency;
- color, material, size and dimensions where supplied;
- product descriptions and care information;
- images;
- variants;
- stock/Add to Bag, pre-order, personalization or store-reservation state.

All fields are time-sensitive. A URL, catalog entry or displayed price alone does not prove orderability.

## 9. Structured Data

Stable JSON-LD `Product`, schema.org `Offer`, SKU, `priceCurrency`, `availability`, variants and canonical markup were not independently confirmed across the four routes through this limited normal-access review. No raw-source probing or browser automation was used.

`structured_data` is not recommended. Use `url_manual`.

## 10. API

No documented public Product, developer, inventory, price, affiliate or partner API/feed was confirmed. Demandware storefront and browser-internal routes are not public APIs and must not be reused.

```text
official_api_available=false
```

## 11. Terms

Official sales terms state that orders are exclusively for individual consumers, personal use or gifts, and not for resale or commercial activity. They expressly prohibit resale/distribution of products purchased from loewe.com and permit cancellation where commercial activity is indicated.

Site content may only be copied for private, personal and non-commercial use; reproduction, distribution, publication, transmission, modification, sale and derivative works are restricted without authorization. No permission for scraping, crawling, automated extraction or commercial product-database reuse was confirmed. Set `terms_status=restricted`; this is a conservative platform policy rather than legal advice.

## 12. robots

`https://www.loewe.com/robots.txt` was retrieved once through normal access. It restricts account/customer/history, cart, shipping, billing, payment, order confirmation, wishlist/login, search, filters/parameters, product variation and Demandware routes. It publishes regional sitemap indexes.

Set `robots_status=restricted`. Robots directives do not grant contractual authorization to automate public pages.

## 13. Shipping

LOEWE’s global shipping table includes Japan, but its terms require country/region selection to display the correct currency, payment and shipping conditions. France-specific terms describe French delivery, while the Japanese destination has its own regional checkout context. The research did not confirm that an EUR EU-locale basket remains an EU order when shipped to Japan.

For the four EU Supplier records use `ships_to_japan=false`. A separately researched Japanese/global Supplier could model Japan delivery; do not merge that fact into these EU records.

## 14. VAT

EU prices include applicable VAT/taxes. No reviewed official material confirms an EU export checkout price, VAT removal, tax-free handling or VAT refund when sourcing through these locale records. Use:

```text
vat_policy=not_refunded
vat_rate=null
```

Do not infer `vat_rate` from general country tax rates.

## 15. BUYMA Considerations

Keep `buyma_allowed_status=unchecked`. Official direct-commerce status does not prove BUYMA acceptance. Human review must cover current BUYMA sourcing rules, invoice/receipt requirements, the explicit resale prohibition, destination/region selection, VAT assumptions, availability, return restrictions and product-specific purchase state.

## 16. Recommended Supplier Policy

Apply to France, Germany, Italy and Spain:

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
robots_status=restricted
official_api_available=false
parser_key=null
request_interval_seconds=null
```

`authorized_retailer` is the closest current enum for a brand-operated official store; it does not mean BUYMA-approved.

## 17. Ingestion Recommendation

Allow only operator-entered public URLs with evidence timestamps. Do not add a parser, browser automation, login/session collection, internal endpoint access, stock monitor, price monitor or scheduled fetch. Price, destination, restriction and availability must be verified manually for each candidate.

## 18. Comparison with existing luxury brands

| Brand | Brand default assessment | Category override | Product-level pattern | EU to Japan | VAT refund | Terms/resale | Automated ingestion |
|---|---|---|---|---|---|---|---|
| Hermès | Conservative/research-oriented | Category differences can be material | Strong product review | Not established | Not established | Restricted | Disabled |
| CHANEL | Category-limited | Material category differences | Category and product dependent | Not established | Not established | Restricted | Disabled |
| Gucci | Limited | No evidenced seed need | Product review required | Not established | Not established | Restricted | Disabled |
| Prada | Limited | No evidenced seed need | Pre-order/personalized possible | No | Not established | Restricted | Disabled |
| Saint Laurent | Limited | No evidenced seed need | Pre-order/personalized explicit | No | Not established | Restricted | Disabled |
| Bottega Veneta | Limited | No evidenced seed need | Pre-order/personalized/boutique states | No | Not established | Restricted | Disabled |
| LOEWE | Recommend `limited` | No evidenced seed need | Pre-order/personalized explicit | EU/EUR checkout not confirmed | Not established | Resale expressly prohibited | Disabled |

LOEWE’s global shipping coverage differs from country-only storefronts, but destination-driven checkout prevents treating global Japan delivery as EU Supplier direct shipping.

## 19. Unresolved Items

- Legal/operator assessment of the explicit resale prohibition and BUYMA use.
- Current BUYMA sourcing eligibility and invoice requirements.
- Whether any contracted affiliate/partner feed exists.
- Per-product canonical/JSON-LD stability.
- Exact checkout transition and currency when Japan is selected.
- Watches and beauty category availability.
- VAT export/refund treatment under any separately approved route.
- Current product/variant availability and restriction state.

## 20. Sources / Checked Date

- France terms: https://www.loewe.com/eur/fr/terms-and-conditions
- Italy terms: https://www.loewe.com/eur/it/terms-and-conditions
- France shipping and returns: https://www.loewe.com/eur/fr/sr
- Italy shipping and returns: https://www.loewe.com/eur/it/sr
- Spain delivery table: https://www.loewe.com/eur/es/cc
- robots: https://www.loewe.com/robots.txt
- France women’s catalog: https://www.loewe.com/eur/fr/femme/
- France fragrance catalog: https://www.loewe.com/eur/fr/femme/parfums
- France eyewear catalog: https://www.loewe.com/eur/fr/femme/accessoires/lunettes-de-soleil
- Spain personalization: https://www.loewe.com/eur/es/personalisation

Checked on 2026-08-15 using minimal normal public access. No CAPTCHA, Cloudflare or access-control bypass, browser automation, login scraping, proxy rotation, internal API use, disguised User-Agent, automated fetch or bulk request was used.
