# Rakuten Advertising Product Search

`RakutenProductSearchClient` implements the official Rakuten Advertising Product Search API without enabling any advertiser integration by default.

Official references:

- `https://developers.rakutenadvertising.com/guides/product_search`
- `https://developers.rakutenadvertising.com/guides/product_search/reference`
- `https://developers.rakutenadvertising.com/guides/access_tokens`

The client requires a bearer token at runtime and never reads one from source-controlled configuration. Callers must obtain it from an approved secret store. Do not put tokens in Git, supplier notes, database payloads, URLs, logs, screenshots, or test fixtures.

Administrators manage the token from **External integrations** in the management console. The API endpoints are `GET`, `PUT`, and `DELETE /integration-settings/rakuten`. They expose only whether a token is configured; the stored value is never returned. Development uses the configured Redis secret store and production uses encrypted SSM Parameter Store at `/buyma-ai/{environment}/integrations/rakuten/product-search-token`.

Saving a token does not make a live Rakuten request or enable a supplier. Keep synchronization disabled until the advertiser has approved the intended use.

## Mytheresa supplier configuration

Administrators can store a Mytheresa advertiser MID and synchronization limits from the Supplier screen. Configuration is stored separately from the Supplier record. The initial approval state is `pending` and synchronization is disabled.

Synchronization remains blocked unless every gate is satisfied: advertiser status is `approved`, the integration switch is enabled, the Supplier is active, automated fetching is enabled, the ingestion source is `official_api`, official API availability is confirmed, terms status is `allowed`, and the Rakuten API token is configured. Database constraints also prohibit enabling synchronization for an unapproved advertiser. Saving or deleting this configuration never calls Rakuten and no scheduler consumes it yet.

Implemented safeguards:

- fixed HTTPS endpoint with environment proxies disabled;
- advertiser `mid` required on every search;
- response products rejected when their advertiser ID differs from the requested `mid`;
- supported search characters and page sizes validated before network access;
- client-side limit of 100 requests per 60 seconds;
- bounded retries for timeouts, transport failures, HTTP 408, 429, and 5xx;
- `Retry-After` honored up to 60 seconds;
- streaming response size limit;
- DTD/entity-bearing and malformed XML rejected;
- safe application error messages that do not contain tokens or response bodies;
- pagination capped by the caller.

The client is currently covered only by mocked responses. No Rakuten or Mytheresa request is made by the test suite. Live connection, secret-store wiring, MID configuration, supplier activation, and scheduled synchronization remain disabled until the relevant advertiser approves the intended data use.
