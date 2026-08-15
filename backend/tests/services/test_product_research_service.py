from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import AppException, NotFoundException
from app.services.product_research_service import ProductResearchService
from app.services.supplier_service import SupplierService


def test_calculate_keeps_vat_policy_as_text():
    result = ProductResearchService.calculate(
        {
            "supplier_price": Decimal("1200"),
            "vat_policy": "excluded_for_export",
            "vat_rate": Decimal("0.20"),
            "exchange_rate": Decimal("165"),
            "japan_shipping_cost": Decimal("5000"),
            "estimated_import_cost": Decimal("10000"),
            "estimated_other_cost": Decimal("3000"),
            "buyma_price": Decimal("300000"),
            "buyma_fee_rate": Decimal("0.077"),
        }
    )

    assert result.export_price == Decimal("1000.00")


def test_prohibited_supplier_cannot_be_ready_for_listing():
    supplier = SimpleNamespace(buyma_allowed_status="prohibited", ships_to_japan=True)
    brand = SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal")
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(supplier, brand, "ready_for_listing")
    assert error.value.code == "SUPPLIER_PROHIBITED"


def test_supplier_not_shipping_to_japan_cannot_be_ready_for_listing():
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=False)
    brand = SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal")
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(supplier, brand, "ready_for_listing")
    assert error.value.code == "SUPPLIER_DOES_NOT_SHIP_TO_JAPAN"


@pytest.mark.asyncio
async def test_candidate_idor_returns_not_found():
    repository = SimpleNamespace(find_by_id_and_owner=_return(None))
    service = ProductResearchService(repository, SimpleNamespace())
    with pytest.raises(NotFoundException):
        await service.require_access(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_supplier_idor_returns_not_found():
    service = SupplierService(SimpleNamespace(find_by_id_and_owner=_return(None)), SimpleNamespace())
    with pytest.raises(NotFoundException):
        await service.require_access(uuid4(), uuid4())


@pytest.mark.parametrize(
    ("brand", "kwargs", "code"),
    [
        (SimpleNamespace(is_research_enabled=False, online_purchase_policy="normal"), {}, "BRAND_RESEARCH_DISABLED"),
        (SimpleNamespace(is_research_enabled=True, online_purchase_policy="research_only"), {}, "BRAND_RESEARCH_ONLY"),
        (SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal"), {"online_purchase_available": False}, "ONLINE_PURCHASE_UNAVAILABLE"),
        (SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal"), {"availability_status": "out_of_stock"}, "PRODUCT_OUT_OF_STOCK"),
    ],
)
def test_extended_ready_for_listing_rules(brand, kwargs, code):
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=True)
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(supplier, brand, "ready_for_listing", **kwargs)
    assert error.value.code == code


def _return(value):
    async def inner(*args, **kwargs):
        return value
    return inner
