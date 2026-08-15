from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.common.exceptions import AppException, NotFoundException
from app.schemas.supplier_policy_evidence import SupplierPolicyEvidenceCreate
from app.services.supplier_policy_evidence_service import SupplierPolicyEvidenceService


def supplier(**overrides):
    values = {
        "id": uuid4(), "owner_user_id": uuid4(), "terms_status": "unknown",
        "robots_status": "restricted", "vat_policy": "not_refunded",
        "ships_to_japan": False, "official_api_available": False,
        "buyma_allowed_status": "unchecked", "ingestion_source_type": "url_manual",
        "automated_fetch_enabled": False,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def user(role="user"):
    return SimpleNamespace(id=uuid4(), role=role)


def payload(**overrides):
    values = {
        "evidence_type": "terms", "result": "restricted",
        "source_url": "https://policy.example.invalid/terms", "source_title": "Terms",
        "source_excerpt": None, "evidence_notes": "Terms restrict commercial use.",
        "checked_at": datetime.now(timezone.utc) - timedelta(days=1),
    }
    values.update(overrides)
    return SupplierPolicyEvidenceCreate(**values)


@pytest.mark.asyncio
async def test_create_uses_current_user_and_snapshot_without_updating_supplier():
    current_user = user()
    current_supplier = supplier()
    repository = SimpleNamespace(create=AsyncMock(side_effect=lambda values: SimpleNamespace(**values)))
    supplier_service = SimpleNamespace(require_access=AsyncMock(return_value=current_supplier))
    service = SupplierPolicyEvidenceService(repository, supplier_service)
    before = current_supplier.terms_status

    created = await service.create(current_supplier.id, payload(), current_user)

    assert created.checked_by_user_id == current_user.id
    assert created.owner_user_id == current_supplier.owner_user_id
    assert created.policy_snapshot["terms_status"] == "unknown"
    assert current_supplier.terms_status == before
    assert created.source_url == "https://policy.example.invalid/terms"


@pytest.mark.asyncio
@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "http://localhost/terms", "http://127.0.0.1/terms",
    "http://169.254.169.254/latest/meta-data", "https://user:secret@example.com/terms",
])
async def test_create_rejects_unsafe_source_urls(url):
    service = SupplierPolicyEvidenceService(
        SimpleNamespace(create=AsyncMock()),
        SimpleNamespace(require_access=AsyncMock(return_value=supplier())),
    )
    with pytest.raises(AppException):
        await service.create(uuid4(), payload(source_url=url), user())
    service.repository.create.assert_not_awaited()


def test_schema_rejects_far_future_checked_at_and_limits_notes():
    with pytest.raises(ValidationError):
        payload(checked_at=datetime.now(timezone.utc) + timedelta(hours=1))
    with pytest.raises(ValidationError):
        payload(evidence_notes="x" * 4001)


def test_schema_rejects_result_that_does_not_match_evidence_type():
    with pytest.raises(ValidationError):
        payload(evidence_type="vat", result="restricted")


@pytest.mark.asyncio
async def test_require_access_returns_404_for_missing_or_inaccessible_evidence():
    service = SupplierPolicyEvidenceService(
        SimpleNamespace(find_for_supplier=AsyncMock(return_value=None)),
        SimpleNamespace(require_access=AsyncMock(return_value=supplier())),
    )
    with pytest.raises(NotFoundException):
        await service.require_access(uuid4(), uuid4(), user())


@pytest.mark.asyncio
async def test_summary_detects_match_mismatch_and_missing_evidence():
    checked = datetime.now(timezone.utc) - timedelta(days=10)
    current_supplier = supplier(terms_status="restricted", robots_status="unknown")
    latest = {
        "terms": SimpleNamespace(id=uuid4(), result="restricted", checked_at=checked),
        "robots": SimpleNamespace(id=uuid4(), result="restricted", checked_at=checked),
    }
    service = SupplierPolicyEvidenceService(
        SimpleNamespace(latest_by_type=AsyncMock(return_value=latest)),
        SimpleNamespace(require_access=AsyncMock(return_value=current_supplier)),
    )
    summary = await service.summary(current_supplier.id, user(), max_age_days=30)
    assert summary["terms"]["consistent"] is True
    assert summary["robots"]["consistent"] is False
    assert summary["vat"]["consistent"] is None
    assert summary["vat"]["latest_evidence"] is None
    assert summary["terms"]["is_stale"] is False


def test_freshness_threshold_is_configurable():
    checked = datetime.now(timezone.utc) - timedelta(days=31)
    assert SupplierPolicyEvidenceService.is_review_due(checked, 30) is True
    assert SupplierPolicyEvidenceService.is_review_due(checked, 60) is False


@pytest.mark.asyncio
async def test_new_evidence_is_appended_and_does_not_overwrite_history():
    records = []

    async def append(values):
        item = SimpleNamespace(id=uuid4(), **values)
        records.append(item)
        return item

    current_supplier = supplier()
    service = SupplierPolicyEvidenceService(
        SimpleNamespace(create=AsyncMock(side_effect=append)),
        SimpleNamespace(require_access=AsyncMock(return_value=current_supplier)),
    )
    await service.create(current_supplier.id, payload(result="unknown"), user())
    await service.create(current_supplier.id, payload(result="restricted"), user())
    assert [item.result for item in records] == ["unknown", "restricted"]
