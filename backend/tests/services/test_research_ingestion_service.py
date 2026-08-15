from types import SimpleNamespace
from decimal import Decimal
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
            "supplier,brand,product_url,product_name,supplier_product_code,supplier_price,currency,availability,buyma_price,purchase_restriction",
            "E2E Shop,E2E Brand,https://example-e2e-shop.invalid/products/valid,Valid Product,SKU-1,1200,EUR,in_stock,300000,client_advisor_only",
            "E2E Shop,E2E Brand,https://example-e2e-shop.invalid/products/invalid,Invalid Product,SKU-2,not-a-price,EUR,in_stock,,normal",
            "E2E Shop,E2E Brand,https://example-e2e-shop.invalid/products/valid,Duplicate Product,SKU-1,1200,EUR,in_stock,300000,normal",
        ]
    ).encode()

    result = await service.import_csv(csv_content, uuid4(), is_admin=True)

    assert [row["status"] for row in result] == [
        "success",
        "failed",
        "duplicate",
    ]
    assert repository.create.await_count == 1
    assert repository.create.await_args.args[0]["purchase_restriction"] == "client_advisor_only"
    repository.db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_csv_purchase_restriction_is_optional():
    brand = SimpleNamespace(id=uuid4())
    supplier = SimpleNamespace(id=uuid4(), website_url="https://shop.invalid", brands=[brand])
    repository = SimpleNamespace(find_duplicate=AsyncMock(return_value=None), create=AsyncMock(return_value=SimpleNamespace(id=uuid4())), db=SimpleNamespace(rollback=AsyncMock()))
    service = ResearchIngestionService(repository, SimpleNamespace(find_by_name=AsyncMock(return_value=supplier)), SimpleNamespace(find_by_name=AsyncMock(return_value=brand)), SimpleNamespace())
    content = "\n".join([
        "supplier,brand,product_url,product_name,supplier_product_code,supplier_price,currency,availability",
        "Shop,Brand,https://shop.invalid/a,A,A,10,EUR,in_stock",
    ]).encode()
    result = await service.import_csv(content, uuid4(), is_admin=True)
    assert result[0]["status"] == "success"
    assert repository.create.await_args_list[0].args[0]["purchase_restriction"] == "unknown"


@pytest.mark.asyncio
async def test_invalid_csv_purchase_restriction_fails_only_its_row():
    brand = SimpleNamespace(id=uuid4())
    supplier = SimpleNamespace(id=uuid4(), website_url="https://shop.invalid", brands=[brand])
    repository = SimpleNamespace(find_duplicate=AsyncMock(return_value=None), create=AsyncMock(), db=SimpleNamespace(rollback=AsyncMock()))
    service = ResearchIngestionService(repository, SimpleNamespace(find_by_name=AsyncMock(return_value=supplier)), SimpleNamespace(find_by_name=AsyncMock(return_value=brand)), SimpleNamespace())
    content = "\n".join([
        "supplier,brand,product_url,product_name,supplier_product_code,supplier_price,currency,availability,purchase_restriction",
        "Shop,Brand,https://shop.invalid/b,B,B,10,EUR,in_stock,not_a_policy",
    ]).encode()
    result = await service.import_csv(content, uuid4(), is_admin=True)
    assert result[0]["status"] == "failed"
    repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_source_purchase_restriction_is_inherited_by_candidate():
    source = SimpleNamespace(
        id=uuid4(), candidate_id=None, brand_id=uuid4(), category_id=None,
        supplier_id=uuid4(), source_url="https://shop.invalid/item",
        external_product_id="SKU", normalized_title="Bag",
        normalized_price=Decimal("100"), normalized_currency="EUR",
        normalized_availability="in_stock", purchase_restriction="client_advisor_only",
        processing_status="matched",
    )
    supplier = SimpleNamespace(id=source.supplier_id, vat_policy="unknown", vat_rate=None, japan_shipping_cost=0)
    candidate_repository = SimpleNamespace(create=AsyncMock(side_effect=lambda values: SimpleNamespace(id=uuid4(), **values)))
    repository = SimpleNamespace(db=SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock()))
    service = ResearchIngestionService(repository, SimpleNamespace(find_by_id=AsyncMock(return_value=supplier)), SimpleNamespace(), candidate_repository)
    payload = SimpleNamespace(exchange_rate=Decimal("160"), buyma_price=Decimal("30000"), buyma_fee_rate=Decimal("0.077"), estimated_import_cost=Decimal("0"), estimated_other_cost=Decimal("0"), japan_shipping_cost=None)

    await service.create_candidate(source, payload, uuid4(), is_admin=True)

    assert candidate_repository.create.await_args.args[0]["purchase_restriction"] == "client_advisor_only"
    assert source.processing_status == "candidate_created"
