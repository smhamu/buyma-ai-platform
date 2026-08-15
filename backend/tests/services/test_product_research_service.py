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
        ProductResearchService.validate_listing_status(supplier, brand, "ready_for_listing", purchase_restriction="normal")
    assert error.value.code == "SUPPLIER_PROHIBITED"


def test_supplier_not_shipping_to_japan_cannot_be_ready_for_listing():
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=False)
    brand = SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal")
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(supplier, brand, "ready_for_listing", purchase_restriction="normal")
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
        ProductResearchService.validate_listing_status(supplier, brand, "ready_for_listing", purchase_restriction="normal", **kwargs)
    assert error.value.code == code


@pytest.mark.parametrize(
    "restriction",
    ["pre_order", "personalized", "made_to_order", "client_advisor_only", "boutique_only", "research_only", "unknown", None],
)
def test_product_purchase_restrictions_fail_closed(restriction):
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=True)
    brand = SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal")
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(
            supplier, brand, "ready_for_listing", purchase_restriction=restriction
        )
    assert error.value.code == "PRODUCT_PURCHASE_RESTRICTED"


def test_normal_product_restriction_allows_ready_for_listing():
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=True)
    brand = SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal")
    ProductResearchService.validate_listing_status(
        supplier, brand, "ready_for_listing", purchase_restriction="normal"
    )


def test_out_of_stock_remains_distinct_from_purchase_restriction():
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=True)
    brand = SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal")
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(
            supplier, brand, "ready_for_listing", availability_status="out_of_stock",
            purchase_restriction="unknown",
        )
    assert error.value.code == "PRODUCT_OUT_OF_STOCK"


def test_category_restriction_is_not_overridden_by_normal_product():
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=True)
    brand = SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal")
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(
            supplier, brand, "ready_for_listing", purchase_restriction="normal",
            resolved_policy="boutique_only", policy_source="category_override",
        )
    assert error.value.code == "CATEGORY_PURCHASE_RESTRICTED"


def _return(value):
    async def inner(*args, **kwargs):
        return value
    return inner
