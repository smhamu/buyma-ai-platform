from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.common.exceptions import AppException
from app.services.brand_category_policy_service import BrandCategoryPolicyService
from app.services.product_research_service import ProductResearchService


@pytest.mark.asyncio
async def test_resolution_uses_category_override():
    brand = SimpleNamespace(online_purchase_policy="research_only", is_research_enabled=True)
    category = SimpleNamespace(is_active=True)
    override = SimpleNamespace(online_purchase_policy="normal", research_enabled=True)
    service = BrandCategoryPolicyService(
        SimpleNamespace(find_by_id=AsyncMock(return_value=brand)),
        SimpleNamespace(find_by_id=AsyncMock(return_value=category)),
        SimpleNamespace(find_for_brand_category=AsyncMock(return_value=override)),
    )
    assert await service.resolve(uuid4(), uuid4()) == ("normal", True, "category_override")


@pytest.mark.asyncio
async def test_resolution_falls_back_to_brand():
    brand = SimpleNamespace(online_purchase_policy="limited", is_research_enabled=True)
    service = BrandCategoryPolicyService(
        SimpleNamespace(find_by_id=AsyncMock(return_value=brand)),
        SimpleNamespace(find_by_id=AsyncMock()),
        SimpleNamespace(find_for_brand_category=AsyncMock()),
    )
    assert await service.resolve(uuid4(), None) == ("limited", True, "brand_default")


def test_ready_for_listing_rejects_restricted_category_override():
    supplier = SimpleNamespace(buyma_allowed_status="allowed", ships_to_japan=True)
    brand = SimpleNamespace(is_research_enabled=True, online_purchase_policy="normal")
    with pytest.raises(AppException) as exc:
        ProductResearchService.validate_listing_status(
            supplier, brand, "ready_for_listing", resolved_policy="boutique_only", resolved_research_enabled=True
        )
    assert exc.value.code == "CATEGORY_PURCHASE_RESTRICTED"
