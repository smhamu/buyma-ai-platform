import asyncio
import re
import time
from collections import deque
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import AsyncIterator, Callable
from xml.etree import ElementTree

import httpx

from app.common.exceptions import AppException


RAKUTEN_PRODUCT_SEARCH_URL = "https://api.linksynergy.com/productsearch/1.0"
_UNSUPPORTED_SEARCH_CHARACTERS = re.compile(r"[&=?{}\\()\[\];~|$!><*%]")


@dataclass(frozen=True)
class RakutenProduct:
    advertiser_id: int
    advertiser_name: str
    link_id: str
    sku: str | None
    name: str
    price: Decimal
    currency: str
    product_url: str
    image_url: str | None
    primary_category: str | None
    secondary_category: str | None
    short_description: str | None
    long_description: str | None


@dataclass(frozen=True)
class RakutenProductPage:
    items: list[RakutenProduct]
    total_matches: int
    total_pages: int
    page_number: int


class AsyncRateLimiter:
    def __init__(self, limit: int = 100, period_seconds: float = 60.0, *, clock: Callable[[], float] = time.monotonic, sleep=asyncio.sleep):
        self.limit = max(1, limit)
        self.period_seconds = max(0.001, period_seconds)
        self.clock, self.sleep = clock, sleep
        self._calls: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = self.clock()
                while self._calls and now - self._calls[0] >= self.period_seconds:
                    self._calls.popleft()
                if len(self._calls) < self.limit:
                    self._calls.append(now)
                    return
                await self.sleep(max(0.0, self.period_seconds - (now - self._calls[0])))


class RakutenProductSearchClient:
    def __init__(
        self,
        token: str,
        *,
        http_client: httpx.AsyncClient | None = None,
        rate_limiter: AsyncRateLimiter | None = None,
        timeout_seconds: float = 15.0,
        max_attempts: int = 3,
        max_response_bytes: int = 2_000_000,
        sleep=asyncio.sleep,
    ):
        if not token or not token.strip():
            raise ValueError("A Rakuten Advertising bearer token is required.")
        self._token = token.strip()
        self._http_client = http_client
        self._owns_client = http_client is None
        self.rate_limiter = rate_limiter or AsyncRateLimiter()
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max(1, max_attempts)
        self.max_response_bytes = max_response_bytes
        self.sleep = sleep

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout_seconds, trust_env=False, follow_redirects=False)
        return self._http_client

    @staticmethod
    def _validate_search_term(value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or len(value) > 200 or _UNSUPPORTED_SEARCH_CHARACTERS.search(value):
            raise AppException(422, "INVALID_RAKUTEN_SEARCH_TERM", "The Rakuten search term is invalid.")
        return value

    async def search(
        self,
        *,
        advertiser_id: int,
        keyword: str | None = None,
        exact: str | None = None,
        category: str | None = None,
        language: str = "en_US",
        max_results: int = 100,
        page_number: int = 1,
    ) -> RakutenProductPage:
        if advertiser_id <= 0:
            raise AppException(422, "INVALID_RAKUTEN_ADVERTISER", "A positive Rakuten advertiser ID is required.")
        if keyword is not None and exact is not None:
            raise AppException(422, "INVALID_RAKUTEN_SEARCH", "Use either keyword or exact search, not both.")
        if language not in {"en_US", "fr_FR", "de_DE", "pt_BR"}:
            raise AppException(422, "INVALID_RAKUTEN_LANGUAGE", "The Rakuten language is not supported.")
        if not 1 <= max_results <= 100 or page_number < 1:
            raise AppException(422, "INVALID_RAKUTEN_PAGE", "Rakuten pagination values are invalid.")
        params = {"mid": advertiser_id, "language": language, "max": max_results, "pagenumber": page_number}
        for key, value in (("keyword", keyword), ("exact", exact), ("cat", category)):
            validated = self._validate_search_term(value)
            if validated is not None:
                params[key] = validated
        response = await self._request(params)
        page = self.parse_response(response.content)
        if any(product.advertiser_id != advertiser_id for product in page.items):
            raise AppException(502, "RAKUTEN_ADVERTISER_MISMATCH", "Rakuten Product Search returned products from another advertiser.")
        return page

    async def iter_pages(self, *, max_pages: int = 100, **search_kwargs) -> AsyncIterator[RakutenProductPage]:
        if not 1 <= max_pages <= 100:
            raise AppException(422, "INVALID_RAKUTEN_PAGE_LIMIT", "Rakuten page limit must be between 1 and 100.")
        page_number = int(search_kwargs.pop("page_number", 1))
        for _ in range(max_pages):
            page = await self.search(page_number=page_number, **search_kwargs)
            yield page
            if page.page_number >= page.total_pages:
                return
            page_number += 1

    async def _request(self, params: dict) -> httpx.Response:
        client = self._client()
        for attempt in range(1, self.max_attempts + 1):
            await self.rate_limiter.acquire()
            try:
                request = client.build_request(
                    "GET", RAKUTEN_PRODUCT_SEARCH_URL, params=params,
                    headers={"Authorization": f"Bearer {self._token}", "Accept": "application/xml"},
                )
                response = await client.send(request, stream=True)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt == self.max_attempts:
                    raise AppException(503, "RAKUTEN_TRANSPORT_ERROR", "Rakuten Product Search is temporarily unavailable.") from exc
                await self.sleep(2 ** (attempt - 1))
                continue
            try:
                if response.status_code in {401, 403}:
                    raise AppException(502, "RAKUTEN_AUTH_ERROR", "Rakuten Product Search authentication failed.")
                if response.status_code == 429 or response.status_code == 408 or response.status_code >= 500:
                    if attempt == self.max_attempts:
                        raise AppException(503, "RAKUTEN_TEMPORARY_ERROR", "Rakuten Product Search is temporarily unavailable.")
                    retry_after = response.headers.get("Retry-After", "")
                    delay = int(retry_after) if retry_after.isdigit() else 2 ** (attempt - 1)
                    await self.sleep(min(max(delay, 0), 60))
                    continue
                if response.status_code != 200:
                    raise AppException(502, "RAKUTEN_API_ERROR", "Rakuten Product Search rejected the request.")
                chunks, size = [], 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > self.max_response_bytes:
                        raise AppException(502, "RAKUTEN_RESPONSE_TOO_LARGE", "Rakuten Product Search returned too much data.")
                    chunks.append(chunk)
                return httpx.Response(200, headers=response.headers, content=b"".join(chunks), request=request)
            finally:
                await response.aclose()
        raise AppException(503, "RAKUTEN_TEMPORARY_ERROR", "Rakuten Product Search is temporarily unavailable.")

    @staticmethod
    def parse_response(content: bytes) -> RakutenProductPage:
        if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
            raise AppException(502, "INVALID_RAKUTEN_RESPONSE", "Rakuten Product Search returned unsafe XML.")
        try:
            root = ElementTree.fromstring(content)
        except ElementTree.ParseError as exc:
            raise AppException(502, "INVALID_RAKUTEN_RESPONSE", "Rakuten Product Search returned invalid XML.") from exc

        def local(element): return element.tag.rsplit("}", 1)[-1]
        def children(element, name): return [item for item in element if local(item) == name]
        def child(element, name):
            match = next(iter(children(element, name)), None)
            return match
        def text(element, name, default=""):
            match = child(element, name)
            return (match.text or "").strip() if match is not None else default
        def integer(element, name):
            try: return int(text(element, name, "0"))
            except ValueError as exc: raise AppException(502, "INVALID_RAKUTEN_RESPONSE", "Rakuten Product Search returned invalid pagination.") from exc

        items = []
        for item in (element for element in root.iter() if local(element) == "item"):
            price_element = child(item, "saleprice")
            if price_element is None or not (price_element.text or "").strip():
                price_element = child(item, "price")
            try:
                price = Decimal((price_element.text or "").strip()) if price_element is not None else Decimal("0")
                advertiser_id = int(text(item, "mid"))
            except (InvalidOperation, ValueError) as exc:
                raise AppException(502, "INVALID_RAKUTEN_RESPONSE", "Rakuten Product Search returned invalid product data.") from exc
            currency = (price_element.attrib.get("currency", "") if price_element is not None else "").upper()
            name, product_url = text(item, "productname"), text(item, "linkurl")
            if advertiser_id <= 0 or not name or not price.is_finite() or price <= 0 or len(currency) != 3 or not product_url.startswith("https://"):
                raise AppException(502, "INVALID_RAKUTEN_RESPONSE", "Rakuten Product Search returned incomplete product data.")
            category, description = child(item, "category"), child(item, "description")
            items.append(RakutenProduct(
                advertiser_id=advertiser_id,
                advertiser_name=text(item, "merchantname"),
                link_id=text(item, "linkid"),
                sku=text(item, "sku") or None,
                name=name,
                price=price,
                currency=currency,
                product_url=product_url,
                image_url=text(item, "imageurl") or None,
                primary_category=text(category, "primary") or None if category is not None else None,
                secondary_category=text(category, "secondary") or None if category is not None else None,
                short_description=text(description, "short") or None if description is not None else None,
                long_description=text(description, "long") or None if description is not None else None,
            ))
        total_matches, total_pages, page_number = integer(root, "TotalMatches"), integer(root, "TotalPages"), integer(root, "PageNumber")
        if total_matches < 0 or total_pages < 0 or page_number < 1:
            raise AppException(502, "INVALID_RAKUTEN_RESPONSE", "Rakuten Product Search returned invalid pagination.")
        return RakutenProductPage(items, total_matches, total_pages, page_number)
