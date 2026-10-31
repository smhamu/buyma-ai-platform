from pathlib import Path

import httpx
import pytest

from app.common.exceptions import AppException
from app.research_providers.rakuten import AsyncRateLimiter, RakutenProductSearchClient


FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parses_official_product_search_xml_fields():
    page = RakutenProductSearchClient.parse_response(fixture("rakuten_product_search_page_1.xml"))
    assert (page.total_matches, page.total_pages, page.page_number) == (2, 2, 1)
    product = page.items[0]
    assert product.advertiser_id == 43171
    assert product.advertiser_name == "Mytheresa"
    assert product.sku == "SKU-001"
    assert str(product.price) == "950.50"
    assert product.currency == "EUR"
    assert product.primary_category == "Women"
    assert product.secondary_category == "Bags~~Shoulder Bags"


@pytest.mark.asyncio
async def test_search_limits_request_to_advertiser_and_uses_bearer_header():
    def handler(request: httpx.Request):
        assert request.url.host == "api.linksynergy.com"
        assert request.url.params["mid"] == "43171"
        assert request.url.params["keyword"] == "leather bag"
        assert request.url.params["max"] == "25"
        assert request.headers["authorization"] == "Bearer secret-token"
        return httpx.Response(200, content=fixture("rakuten_product_search_page_1.xml"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = RakutenProductSearchClient("secret-token", http_client=http_client)
        page = await client.search(advertiser_id=43171, keyword="leather bag", max_results=25)
    assert len(page.items) == 1


@pytest.mark.asyncio
async def test_iterates_pages_until_reported_last_page():
    requested_pages = []
    def handler(request: httpx.Request):
        page = int(request.url.params["pagenumber"])
        requested_pages.append(page)
        return httpx.Response(200, content=fixture(f"rakuten_product_search_page_{page}.xml"))
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = RakutenProductSearchClient("token", http_client=http_client)
        pages = [page async for page in client.iter_pages(advertiser_id=43171)]
    assert requested_pages == [1, 2]
    assert [item.sku for page in pages for item in page.items] == ["SKU-001", "SKU-002"]


@pytest.mark.asyncio
async def test_retries_rate_limit_and_honors_retry_after():
    calls, delays = 0, []
    def handler(request: httpx.Request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "3"})
        return httpx.Response(200, content=fixture("rakuten_product_search_page_1.xml"))
    async def fake_sleep(value): delays.append(value)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = RakutenProductSearchClient("token", http_client=http_client, sleep=fake_sleep)
        await client.search(advertiser_id=43171)
    assert calls == 2
    assert delays == [3]


@pytest.mark.asyncio
async def test_transport_failure_is_safe_and_never_exposes_token():
    async def handler(request: httpx.Request):
        raise httpx.ConnectError("request failed with Bearer secret-token", request=request)
    async def no_sleep(_): pass
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = RakutenProductSearchClient("secret-token", http_client=http_client, max_attempts=2, sleep=no_sleep)
        with pytest.raises(AppException) as exc:
            await client.search(advertiser_id=43171)
    assert exc.value.code == "RAKUTEN_TRANSPORT_ERROR"
    assert "secret-token" not in str(exc.value.detail)


@pytest.mark.parametrize("content", [b"<not-xml", b"<!DOCTYPE x [<!ENTITY x 'bad'>]><result/>"])
def test_rejects_invalid_or_unsafe_xml(content):
    with pytest.raises(AppException) as exc:
        RakutenProductSearchClient.parse_response(content)
    assert exc.value.code == "INVALID_RAKUTEN_RESPONSE"


@pytest.mark.asyncio
async def test_rate_limiter_waits_after_configured_limit():
    now, waits = [0.0], []
    async def fake_sleep(value):
        waits.append(value)
        now[0] += value
    limiter = AsyncRateLimiter(limit=2, period_seconds=10, clock=lambda: now[0], sleep=fake_sleep)
    await limiter.acquire(); await limiter.acquire(); await limiter.acquire()
    assert waits == [10.0]


@pytest.mark.asyncio
async def test_rejects_unsupported_query_before_network_call():
    client = RakutenProductSearchClient("token", http_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda request: pytest.fail("network called"))))
    try:
        with pytest.raises(AppException) as exc:
            await client.search(advertiser_id=43171, keyword="bag&shoes")
        assert exc.value.code == "INVALID_RAKUTEN_SEARCH_TERM"
    finally:
        await client._http_client.aclose()


@pytest.mark.asyncio
async def test_rejects_products_from_a_different_advertiser():
    xml = fixture("rakuten_product_search_page_1.xml").replace(b"<mid>43171</mid>", b"<mid>99999</mid>")
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=xml))) as http_client:
        client = RakutenProductSearchClient("token", http_client=http_client)
        with pytest.raises(AppException) as exc:
            await client.search(advertiser_id=43171)
    assert exc.value.code == "RAKUTEN_ADVERTISER_MISMATCH"


@pytest.mark.asyncio
async def test_rejects_response_over_streaming_size_limit():
    content = fixture("rakuten_product_search_page_1.xml")
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content))) as http_client:
        client = RakutenProductSearchClient("token", http_client=http_client, max_response_bytes=10)
        with pytest.raises(AppException) as exc:
            await client.search(advertiser_id=43171)
    assert exc.value.code == "RAKUTEN_RESPONSE_TOO_LARGE"
