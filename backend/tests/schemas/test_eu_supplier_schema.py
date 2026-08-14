import pytest
from pydantic import ValidationError

from app.schemas.supplier import SupplierCreate


def test_supported_eu_country_is_accepted():
    supplier = SupplierCreate(name="EU shop", country_code="FR", website_url="https://example.eu")
    assert supplier.country_code == "FR"
    assert supplier.default_currency == "EUR"


def test_uk_is_not_treated_as_an_eu_country():
    with pytest.raises(ValidationError):
        SupplierCreate(name="UK shop", country_code="GB", website_url="https://example.co.uk")
