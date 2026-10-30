import json
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser

from app.common.exceptions import AppException
from app.research_providers.base import FetchedProduct
from app.research_providers.http_client import SafeResearchHttpClient


class _JsonLdExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json_ld = False
        self.parts: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag.lower() == "script" and values.get("type", "").lower() == "application/ld+json":
            self.in_json_ld, self.parts = True, []

    def handle_data(self, data):
        if self.in_json_ld:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.in_json_ld:
            self.blocks.append("".join(self.parts))
            self.in_json_ld = False


class SchemaOrgProductProvider:
    def __init__(self, http_client: SafeResearchHttpClient | None = None):
        self.http_client = http_client or SafeResearchHttpClient()

    @staticmethod
    def _walk(value):
        if isinstance(value, list):
            for item in value:
                yield from SchemaOrgProductProvider._walk(item)
        elif isinstance(value, dict):
            if value.get("@type") == "Product" or "Product" in (value.get("@type") or []):
                yield value
            for item in value.get("@graph", []):
                yield from SchemaOrgProductProvider._walk(item)

    @staticmethod
    def _availability(value: str | None) -> str:
        token = (value or "").rsplit("/", 1)[-1].lower()
        if token in {"instock", "limitedavailability"}: return "in_stock"
        if token in {"outofstock", "soldout", "discontinued"}: return "out_of_stock"
        if token in {"preorder", "presale"}: return "preorder"
        return "unknown"

    @classmethod
    def parse(cls, body: str, content_type: str = "text/html") -> FetchedProduct:
        documents = []
        if content_type in {"application/json", "application/ld+json"}:
            documents = [body]
        else:
            extractor = _JsonLdExtractor(); extractor.feed(body); documents = extractor.blocks
        products = []
        for document in documents:
            try: products.extend(cls._walk(json.loads(document)))
            except (json.JSONDecodeError, TypeError): continue
        if not products:
            raise AppException(422, "PRODUCT_DATA_NOT_FOUND", "No schema.org Product data was found.")
        product = products[0]
        offers = product.get("offers") or {}
        if isinstance(offers, list): offers = next((x for x in offers if isinstance(x, dict) and x.get("price") is not None), {})
        brand = product.get("brand")
        if isinstance(brand, dict): brand = brand.get("name")
        try: price = Decimal(str(offers.get("price")))
        except (InvalidOperation, TypeError): raise AppException(422, "INVALID_PRODUCT_PRICE", "Product price is missing or invalid.")
        title, currency = str(product.get("name") or "").strip(), str(offers.get("priceCurrency") or "").upper()
        brand = str(brand).strip() if brand else None
        if not title or len(title) > 500 or (brand and len(brand) > 255) or not price.is_finite() or price <= 0 or currency not in {"EUR", "JPY", "GBP", "CHF", "USD"}:
            raise AppException(422, "INVALID_PRODUCT_DATA", "Product title, price, or currency is invalid.")
        external_id = product.get("sku") or product.get("productID") or product.get("mpn")
        payload = {"name": title, "brand": brand, "offers": {"price": str(price), "priceCurrency": currency, "availability": offers.get("availability")}, "sku": external_id}
        return FetchedProduct(title, brand, price, currency, cls._availability(offers.get("availability")), str(external_id)[:255] if external_id else None, payload)

    async def fetch_product(self, url: str, supplier) -> FetchedProduct:
        body, content_type = await self.http_client.get(url, supplier.website_url)
        return self.parse(body, content_type)
