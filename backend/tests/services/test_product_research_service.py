from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.common.exceptions import AppException, NotFoundException
from app.services.product_research_service import ProductResearchService
from app.services.supplier_service import SupplierService


def test_prohibited_supplier_cannot_be_ready_for_listing():
    supplier = SimpleNamespace(buyma_allowed_status="prohibited", ships_to_japan=True)
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(supplier, "ready_for_listing")
    assert error.value.code == "SUPPLIER_PROHIBITED"


def test_supplier_not_shipping_to_japan_cannot_be_ready_for_listing():
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=False)
    with pytest.raises(AppException) as error:
        ProductResearchService.validate_listing_status(supplier, "ready_for_listing")
    assert error.value.code == "SUPPLIER_DOES_NOT_SHIP_TO_JAPAN"


@pytest.mark.asyncio
async def test_candidate_idor_returns_not_found():
    repository = SimpleNamespace(find_by_id_and_owner=_return(None))
    service = ProductResearchService(repository, SimpleNamespace())
    with pytest.raises(NotFoundException):
        await service.require_access(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_supplier_idor_returns_not_found():
    service = SupplierService(SimpleNamespace(find_by_id_and_owner=_return(None)))
    with pytest.raises(NotFoundException):
        await service.require_access(uuid4(), uuid4())


def _return(value):
    async def inner(*args, **kwargs):
        return value
    return inner
