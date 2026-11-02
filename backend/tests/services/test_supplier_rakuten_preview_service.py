from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.common.exceptions import AppException
from app.research_providers.rakuten import RakutenProduct, RakutenProductPage
from app.services.supplier_rakuten_preview_service import SupplierRakutenPreviewService


def ready_supplier():
    return SimpleNamespace(
        id=uuid4(), is_active=True, automated_fetch_enabled=True,
        ingestion_source_type="official_api", official_api_available=True, terms_status="allowed",
    )


def ready_config(**overrides):
    values = {
        "approval_status": "approved", "sync_enabled": False, "advertiser_mid": 43171,
        "search_keyword": "shoes", "language": "en_US", "max_results": 25, "max_pages": 3,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class FakeClient:
    instances = []

    def __init__(self, token):
        self.token = token
        self.search = AsyncMock(return_value=RakutenProductPage(
            items=[RakutenProduct(
                advertiser_id=43171, advertiser_name="Mytheresa", link_id="link-1", sku="sku-1",
                name="Leather shoes", price=Decimal("199.95"), currency="EUR",
                product_url="https://www.mytheresa.com/product", image_url="https://img.example/item.jpg",
                primary_category="Shoes", secondary_category="Women", short_description="Description",
                long_description="Long description",
            )], total_matches=1, total_pages=1, page_number=1,
        ))
        self.instances.append(self)

    async def __aenter__(self): return self
    async def __aexit__(self, *_): return None


@pytest.mark.asyncio
async def test_preview_fetches_one_page_without_database_writes_or_token_disclosure():
    supplier, config = ready_supplier(), ready_config()
    config_service = SimpleNamespace(
        require_mytheresa_supplier=AsyncMock(return_value=supplier),
        get=AsyncMock(return_value=config),
    )
    secret_store = SimpleNamespace(get_secret=AsyncMock(return_value="private-token"))
    service = SupplierRakutenPreviewService(config_service, secret_store, "secret-ref", FakeClient)

    result = await service.preview(supplier.id, 1)

    assert result.persisted is False
    assert result.items[0].name == "Leather shoes"
    assert "private-token" not in result.model_dump_json()
    FakeClient.instances[-1].search.assert_awaited_once_with(
        advertiser_id=43171, keyword="shoes", language="en_US", max_results=25, page_number=1
    )
    assert not hasattr(config_service, "commit")


@pytest.mark.asyncio
async def test_preview_is_blocked_before_secret_or_network_access():
    supplier, config = ready_supplier(), ready_config(approval_status="pending")
    config_service = SimpleNamespace(
        require_mytheresa_supplier=AsyncMock(return_value=supplier),
        get=AsyncMock(return_value=config),
    )
    secret_store = SimpleNamespace(get_secret=AsyncMock())
    factory = AsyncMock()
    service = SupplierRakutenPreviewService(config_service, secret_store, "secret-ref", factory)

    with pytest.raises(AppException) as exc:
        await service.preview(supplier.id, 1)

    assert exc.value.code == "RAKUTEN_PREVIEW_BLOCKED"
    secret_store.get_secret.assert_not_awaited()
    factory.assert_not_called()


@pytest.mark.asyncio
async def test_preview_respects_configured_page_limit_before_network_access():
    supplier, config = ready_supplier(), ready_config(max_pages=2)
    config_service = SimpleNamespace(
        require_mytheresa_supplier=AsyncMock(return_value=supplier),
        get=AsyncMock(return_value=config),
    )
    secret_store = SimpleNamespace(get_secret=AsyncMock())
    service = SupplierRakutenPreviewService(config_service, secret_store, "secret-ref", FakeClient)

    with pytest.raises(AppException) as exc:
        await service.preview(supplier.id, 3)

    assert exc.value.code == "RAKUTEN_PREVIEW_PAGE_LIMIT"
    secret_store.get_secret.assert_not_awaited()
