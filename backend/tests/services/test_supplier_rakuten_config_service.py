from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.common.exceptions import AppException
from app.schemas.supplier_rakuten_config import SupplierRakutenConfigUpdate
from app.services.supplier_rakuten_config_service import SupplierRakutenConfigService


def supplier(**overrides):
    values = {
        "id": uuid4(), "website_url": "https://www.mytheresa.com/jp/en/", "is_active": True,
        "automated_fetch_enabled": False, "ingestion_source_type": "manual",
        "official_api_available": False, "terms_status": "unchecked",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def config(**overrides):
    values = {"approval_status": "pending", "sync_enabled": False}
    values.update(overrides)
    return SimpleNamespace(**values)


def test_pending_approval_and_supplier_policy_fail_closed():
    allowed, reasons = SupplierRakutenConfigService.gate(config(), supplier(), token_configured=False)
    assert not allowed
    assert reasons == [
        "advertiser_not_approved", "sync_disabled", "automated_fetch_disabled",
        "official_api_not_selected", "official_api_unavailable", "terms_not_allowed",
        "rakuten_token_missing",
    ]


def test_all_gates_are_required_for_sync():
    item = supplier(
        automated_fetch_enabled=True, ingestion_source_type="official_api",
        official_api_available=True, terms_status="allowed",
    )
    assert SupplierRakutenConfigService.gate(
        config(approval_status="approved", sync_enabled=True), item, token_configured=True
    ) == (True, [])


def test_schema_rejects_enabling_before_approval():
    with pytest.raises(ValueError, match="before advertiser approval"):
        SupplierRakutenConfigUpdate(advertiser_mid=43171, approval_status="pending", sync_enabled=True)


@pytest.mark.asyncio
async def test_only_mytheresa_supplier_is_supported():
    db = SimpleNamespace(scalar=AsyncMock(return_value=supplier(website_url="https://example.com")))
    with pytest.raises(AppException) as exc:
        await SupplierRakutenConfigService(db).require_mytheresa_supplier(uuid4())
    assert exc.value.code == "NOT_MYTHERESA_SUPPLIER"


@pytest.mark.asyncio
async def test_policy_blocks_sync_even_after_advertiser_approval():
    item = supplier()
    db = SimpleNamespace(scalar=AsyncMock(return_value=item))
    payload = SupplierRakutenConfigUpdate(advertiser_mid=43171, approval_status="approved", sync_enabled=True)
    with pytest.raises(AppException) as exc:
        await SupplierRakutenConfigService(db).upsert(item.id, payload, token_configured=True)
    assert exc.value.code == "RAKUTEN_SYNC_POLICY_BLOCKED"


@pytest.mark.asyncio
async def test_token_is_required_before_sync_can_be_enabled():
    item = supplier(
        automated_fetch_enabled=True, ingestion_source_type="official_api",
        official_api_available=True, terms_status="allowed",
    )
    db = SimpleNamespace(scalar=AsyncMock(return_value=item))
    payload = SupplierRakutenConfigUpdate(advertiser_mid=43171, approval_status="approved", sync_enabled=True)
    with pytest.raises(AppException) as exc:
        await SupplierRakutenConfigService(db).upsert(item.id, payload, token_configured=False)
    assert exc.value.code == "RAKUTEN_TOKEN_MISSING"
