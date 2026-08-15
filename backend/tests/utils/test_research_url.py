import pytest

from app.common.exceptions import AppException
from app.utils.research_url import normalize_research_url, validate_supplier_domain


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://localhost/x", "http://127.0.0.1/x", "http://169.254.169.254/latest/meta-data", "http://10.0.0.1/x", "https://user:pass@example.com/x"])
def test_unsafe_research_urls_are_rejected(url):
    with pytest.raises(AppException): normalize_research_url(url)


def test_valid_supplier_url_is_normalized():
    url = normalize_research_url("HTTPS://www.example.com/products/1#details")
    assert url == "https://www.example.com/products/1"
    validate_supplier_domain(url, "https://www.example.com")


def test_different_supplier_domain_is_rejected():
    with pytest.raises(AppException) as error:
        validate_supplier_domain("https://evil.example/product", "https://shop.example")
    assert error.value.code == "SOURCE_DOMAIN_MISMATCH"
