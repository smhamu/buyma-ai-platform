# EU Research Ingestion

Research Ingestion stores auditable source records before they become BUYMA research candidates. It does not fetch external websites in this phase.

## Source types and supplier policy

Supported source types are `manual`, `url_manual`, `csv`, `official_api`, `structured_data`, `html_parser`, and `disabled`. New suppliers default to `manual` with `automated_fetch_enabled=false`. Terms and robots statuses are tracked separately; neither is treated as a legal conclusion.

Automatic fetch is fail-closed. It requires an active supplier, explicit enablement, an automatic source type, terms not marked prohibited, and robots not marked disallowed. BUYMA purchasing status remains a separate decision.

## URL security

Manual URL registration accepts absolute HTTP(S) URLs only. Userinfo, localhost, non-global IP literals, link-local and metadata destinations are rejected. The URL hostname must exactly match the supplier `website_url` hostname; subdomains are not allowed by the current policy. Fragments are removed for duplicate detection. No redirects, DNS resolution, or HTTP requests occur during registration. A future fetcher must re-resolve DNS at connection time, reject every non-global address, validate redirect targets, and pin the validated destination to mitigate DNS rebinding.

## CSV format

UTF-8 CSV files up to 2 MB use these columns:

`supplier,brand,product_url,product_name,supplier_product_code,supplier_price,currency,availability,buyma_price`

`buyma_price` is optional. Import is row-oriented: valid rows are retained and each invalid or duplicate row is reported without rolling back unrelated valid rows. Supplier and Brand must already exist. CSV imports create normalized source records; they do not contact supplier sites.

## Candidate conversion

Only matched sources with supplier, brand, title, price, and currency can be converted. The conversion request supplies the exchange rate and BUYMA price because no FX API is used. VAT policy/rate and default Japan shipping cost are snapshotted from the Supplier, then the existing backend `PriceCalculationService` calculates cost and profit. `source_product_id` is unique, preventing multiple candidates from one source.

## Provider architecture

Future integrations should implement a supplier-specific fetcher boundary with `fetch_product(url)` and `normalize(payload)` operations. Official API, JSON-LD, and explicitly approved HTML parsers must remain separate providers. Do not introduce a universal scraper, CAPTCHA bypass, session scraping, proxy rotation, or anti-bot evasion.

Raw payloads must never contain credentials or session material and must be size-limited before persistence. Production fetchers should run as constrained background jobs with per-supplier rate limits and audit logs.
