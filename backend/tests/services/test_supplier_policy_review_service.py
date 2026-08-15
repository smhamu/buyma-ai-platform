from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.supplier_policy_review_service import SupplierPolicyReviewService


class EvidenceRepository:
    def __init__(self, evidence): self.evidence = evidence
    async def latest_by_type(self, _supplier_id): return self.evidence


def supplier(**overrides):
    values = dict(
        id=uuid4(), name="Test Supplier", country_code="FR", supplier_type="boutique",
        brands=[], updated_at=datetime.now(timezone.utc), terms_status="restricted",
        robots_status="allowed", vat_policy="included", ships_to_japan=True,
        official_api_available=False, buyma_allowed_status="allowed",
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def settings(**overrides):
    values = dict(
        required_evidence_types=["terms"], terms_max_age_days=180, robots_max_age_days=180,
        vat_max_age_days=180, shipping_max_age_days=180, official_api_max_age_days=365,
        buyma_max_age_days=90,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def evidence(result="restricted", days=1):
    return SimpleNamespace(result=result, checked_at=datetime.now(timezone.utc)-timedelta(days=days))


@pytest.mark.asyncio
async def test_review_is_up_to_date_when_required_evidence_matches():
    service=SupplierPolicyReviewService(None,SimpleNamespace(repository=EvidenceRepository({"terms":evidence()}),current_value=lambda s,t: getattr(s,"terms_status") if t=="terms" else "unsupported"))
    result=await service.evaluate(supplier(),settings())
    assert result["overall_status"] == "up_to_date"


@pytest.mark.asyncio
async def test_review_detects_stale_and_disabled_threshold():
    evidence_service=SimpleNamespace(repository=EvidenceRepository({"terms":evidence(days=200)}),current_value=lambda s,t: getattr(s,"terms_status") if t=="terms" else "unsupported")
    assert (await SupplierPolicyReviewService(None,evidence_service).evaluate(supplier(),settings()))["overall_status"] == "review_due"
    assert (await SupplierPolicyReviewService(None,evidence_service).evaluate(supplier(),settings(terms_max_age_days=None)))["overall_status"] == "up_to_date"


@pytest.mark.asyncio
async def test_review_detects_inconsistent_and_no_evidence():
    inconsistent=SimpleNamespace(repository=EvidenceRepository({"terms":evidence("allowed")}),current_value=lambda s,t: getattr(s,"terms_status") if t=="terms" else "unsupported")
    assert (await SupplierPolicyReviewService(None,inconsistent).evaluate(supplier(),settings()))["overall_status"] == "inconsistent"
    missing=SimpleNamespace(repository=EvidenceRepository({}),current_value=lambda s,t: getattr(s,"terms_status") if t=="terms" else "unsupported")
    assert (await SupplierPolicyReviewService(None,missing).evaluate(supplier(),settings()))["overall_status"] == "no_evidence"
    assert (await SupplierPolicyReviewService(None,missing).evaluate(supplier(),settings(required_evidence_types=[])))["overall_status"] == "up_to_date"
