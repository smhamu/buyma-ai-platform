from decimal import Decimal

import pytest

from app.common.exceptions import AppException
from app.research_providers.json_ld import SchemaOrgProductProvider


def test_parses_schema_org_product_from_html():
    html = '''<html><script type="application/ld+json">{
      "@context":"https://schema.org", "@type":"Product", "name":"Leather Bag",
      "sku":"SKU-123", "brand":{"@type":"Brand","name":"Example Brand"},
      "offers":{"@type":"Offer","price":"1250.50","priceCurrency":"EUR","availability":"https://schema.org/InStock"}
    }</script></html>'''

    product = SchemaOrgProductProvider.parse(html)

    assert product.title == "Leather Bag"
    assert product.brand == "Example Brand"
    assert product.price == Decimal("1250.50")
    assert product.currency == "EUR"
    assert product.availability == "in_stock"
    assert product.external_product_id == "SKU-123"
    assert product.raw_payload["offers"]["price"] == "1250.50"


def test_parses_product_inside_json_ld_graph():
    body = '{"@graph":[{"@type":"WebPage"},{"@type":"Product","name":"Shoes","offers":{"price":500,"priceCurrency":"GBP","availability":"OutOfStock"}}]}'
    product = SchemaOrgProductProvider.parse(body, "application/ld+json")
    assert product.title == "Shoes"
    assert product.availability == "out_of_stock"


@pytest.mark.parametrize("body", ["<html></html>", '<script type="application/ld+json">{"@type":"Product","name":"Bag"}</script>'])
def test_rejects_missing_or_incomplete_product_data(body):
    with pytest.raises(AppException):
        SchemaOrgProductProvider.parse(body)


def test_rejects_non_finite_price_and_oversized_title():
    for name, price in (("Bag", "NaN"), ("x" * 501, "10")):
        body = f'{{"@type":"Product","name":"{name}","offers":{{"price":"{price}","priceCurrency":"EUR"}}}}'
        with pytest.raises(AppException) as exc:
            SchemaOrgProductProvider.parse(body, "application/ld+json")
        assert exc.value.code == "INVALID_PRODUCT_DATA"
