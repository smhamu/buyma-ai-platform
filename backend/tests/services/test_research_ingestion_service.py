from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.research_ingestion_service import ResearchIngestionService


def test_automatic_fetch_is_disabled_by_default():
    supplier = SimpleNamespace(is_active=True, automated_fetch_enabled=False, ingestion_source_type="official_api", terms_status="allowed", robots_status="allowed")
    assert not ResearchIngestionService.automatic_fetch_allowed(supplier)


def test_prohibited_terms_and_disallowed_robots_fail_closed():
    base = dict(is_active=True, automated_fetch_enabled=True, ingestion_source_type="html_parser")
    assert not ResearchIngestionService.automatic_fetch_allowed(SimpleNamespace(**base, terms_status="prohibited", robots_status="allowed"))
    assert not ResearchIngestionService.automatic_fetch_allowed(SimpleNamespace(**base, terms_status="allowed", robots_status="disallowed"))


def test_approved_fetch_policy_can_be_enabled_explicitly():
    supplier = SimpleNamespace(is_active=True, automated_fetch_enabled=True, ingestion_source_type="official_api", terms_status="allowed", robots_status="allowed")
    assert ResearchIngestionService.automatic_fetch_allowed(supplier)


@pytest.mark.asyncio
async def test_csv_import_returns_success_failed_and_duplicate_per_row():
    brand = SimpleNamespace(id=uuid4())
    supplier = SimpleNamespace(
        id=uuid4(),
        website_url="https://example-e2e-shop.invalid",
        brands=[brand],
    )
    repository = SimpleNamespace(
        find_duplicate=AsyncMock(side_effect=[None, SimpleNamespace(id=uuid4())]),
        create=AsyncMock(return_value=SimpleNamespace(id=uuid4())),
        db=SimpleNamespace(rollback=AsyncMock()),
    )
    suppliers = SimpleNamespace(find_by_name=AsyncMock(return_value=supplier))
    brands = SimpleNamespace(find_by_name=AsyncMock(return_value=brand))
    service = ResearchIngestionService(
        repository,
        suppliers,
        brands,
        SimpleNamespace(),
    )
    csv_content = "\n".join(
        [
            "supplier,brand,product_url,product_name,supplier_product_code,supplier_price,currency,availability,buyma_price",
            "E2E Shop,E2E Brand,https://example-e2e-shop.invalid/products/valid,Valid Product,SKU-1,1200,EUR,in_stock,300000",
            "E2E Shop,E2E Brand,https://example-e2e-shop.invalid/products/invalid,Invalid Product,SKU-2,not-a-price,EUR,in_stock,",
            "E2E Shop,E2E Brand,https://example-e2e-shop.invalid/products/valid,Duplicate Product,SKU-1,1200,EUR,in_stock,300000",
        ]
    ).encode()

    result = await service.import_csv(csv_content, uuid4(), is_admin=True)

    assert [row["status"] for row in result] == [
        "success",
        "failed",
        "duplicate",
    ]
    assert repository.create.await_count == 1
    repository.db.rollback.assert_awaited_once()
