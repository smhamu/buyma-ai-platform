from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.brand import Brand  # noqa: F401 - registers ORM relationships
from app.models.product_category import BrandCategoryPolicy  # noqa: F401 - registers ORM relationships
from app.models.supplier_policy_evidence import SupplierPolicyEvidence  # noqa: F401 - registers ORM relationships
from app.models.user import User  # noqa: F401 - registers ORM relationships
from app.models.notification_outbox import NotificationOutbox
from app.models.supplier_policy_review_transition import SupplierPolicyReviewTransition
from app.services.supplier_policy_review_state_service import SupplierPolicyReviewStateService


class FakeDb:
    def __init__(self, supplier):
        self.supplier=supplier;self.state=None;self.added=[]
        self.flush=AsyncMock();self.commit=AsyncMock();self.rollback=AsyncMock();self.refresh=AsyncMock()
    async def scalar(self,_query): return self.state
    async def get(self,_model,_id): return self.supplier
    def add(self,item):
        self.added.append(item)
        if item.__class__.__name__ == "SupplierPolicyReviewState": self.state=item


def review(status="no_evidence",terms="no_evidence",robots="up_to_date"):
    return {"overall_status":status,"issue_types":[key for key,value in {"terms":terms,"robots":robots}.items() if value!="up_to_date"],"types":{"terms":{"review_status":terms},"robots":{"review_status":robots}}}


@pytest.mark.asyncio
async def test_initial_state_creates_transition_but_no_outbox_and_same_state_is_idempotent():
    supplier=SimpleNamespace(id=uuid4(),owner_user_id=uuid4(),name="Shop")
    db=FakeDb(supplier);service=SimpleNamespace(settings=AsyncMock(return_value=object()),evaluate=AsyncMock(return_value=review()))
    recorder=SupplierPolicyReviewStateService(db,service)
    first=await recorder.evaluate_and_record_supplier_review(supplier.id)
    assert first["transition"].from_status is None
    assert first["outbox"] is None
    added_before=len(db.added)
    second=await recorder.evaluate_and_record_supplier_review(supplier.id)
    assert second["transition"] is None
    assert len(db.added) == added_before


@pytest.mark.asyncio
async def test_transition_creates_exactly_one_safe_deduplicated_outbox():
    supplier=SimpleNamespace(id=uuid4(),owner_user_id=uuid4(),name="Shop")
    db=FakeDb(supplier);review_service=SimpleNamespace(settings=AsyncMock(return_value=object()),evaluate=AsyncMock(return_value=review()))
    recorder=SupplierPolicyReviewStateService(db,review_service)
    await recorder.evaluate_and_record_supplier_review(supplier.id)
    review_service.evaluate.return_value=review("inconsistent","inconsistent")
    changed=await recorder.evaluate_and_record_supplier_review(supplier.id)
    assert isinstance(changed["transition"],SupplierPolicyReviewTransition)
    assert isinstance(changed["outbox"],NotificationOutbox)
    assert changed["transition"].changed_evidence_types == ["terms"]
    assert changed["outbox"].transition_id == changed["transition"].id
    assert changed["outbox"].dedupe_key.endswith(str(changed["transition"].id))
    assert set(changed["outbox"].payload) == {"supplier_id","supplier_name","from_status","to_status","changed_evidence_types","occurred_at"}
    count=len([item for item in db.added if isinstance(item,NotificationOutbox)])
    await recorder.evaluate_and_record_supplier_review(supplier.id)
    assert len([item for item in db.added if isinstance(item,NotificationOutbox)]) == count


@pytest.mark.asyncio
async def test_same_overall_status_with_type_change_creates_transition():
    supplier=SimpleNamespace(id=uuid4(),owner_user_id=uuid4(),name="Shop")
    db=FakeDb(supplier);review_service=SimpleNamespace(settings=AsyncMock(return_value=object()),evaluate=AsyncMock(return_value=review("review_due","review_due")))
    recorder=SupplierPolicyReviewStateService(db,review_service);await recorder.evaluate_and_record_supplier_review(supplier.id)
    review_service.evaluate.return_value=review("review_due","up_to_date","review_due")
    result=await recorder.evaluate_and_record_supplier_review(supplier.id)
    assert result["transition"].from_status == result["transition"].to_status == "review_due"
    assert result["transition"].changed_evidence_types == ["robots","terms"]


@pytest.mark.asyncio
async def test_commit_failure_rolls_back_state_transition_and_outbox():
    supplier=SimpleNamespace(id=uuid4(),owner_user_id=uuid4(),name="Shop")
    db=FakeDb(supplier);db.commit.side_effect=RuntimeError("database unavailable")
    recorder=SupplierPolicyReviewStateService(db,SimpleNamespace(settings=AsyncMock(return_value=object()),evaluate=AsyncMock(return_value=review())))
    with pytest.raises(RuntimeError): await recorder.evaluate_and_record_supplier_review(supplier.id)
    db.rollback.assert_awaited_once()
