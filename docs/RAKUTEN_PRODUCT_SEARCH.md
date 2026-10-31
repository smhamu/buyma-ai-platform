# Rakuten Advertising Product Search

`RakutenProductSearchClient` implements the official Rakuten Advertising Product Search API without enabling any advertiser integration by default.

Official references:

- `https://developers.rakutenadvertising.com/guides/product_search`
- `https://developers.rakutenadvertising.com/guides/product_search/reference`
- `https://developers.rakutenadvertising.com/guides/access_tokens`

The client requires a bearer token at runtime and never reads one from source-controlled configuration. Callers must obtain it from an approved secret store. Do not put tokens in Git, supplier notes, database payloads, URLs, logs, screenshots, or test fixtures.

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
