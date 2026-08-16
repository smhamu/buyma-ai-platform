from app.workers import supplier_policy_review_tasks
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest


def test_scheduled_review_task_returns_batch_result(monkeypatch):
    async def fake_evaluate(): return {"evaluated_count":3,"failed_count":1,"failed_supplier_ids":["safe-id"]}
    monkeypatch.setattr(supplier_policy_review_tasks,"_evaluate_supplier_policy_reviews",fake_evaluate)
    assert supplier_policy_review_tasks.evaluate_supplier_policy_reviews_task.run() == {"evaluated_count":3,"failed_count":1,"failed_supplier_ids":["safe-id"]}


@pytest.mark.asyncio
async def test_batch_continues_after_one_supplier_failure(monkeypatch):
    supplier_ids=[uuid4(),uuid4(),uuid4()]
    class ScalarResult:
        def all(self): return supplier_ids
    class Db:
        rollback=AsyncMock()
        async def scalars(self,_query): return ScalarResult()
        async def __aenter__(self): return self
        async def __aexit__(self,*_args): return None
    class Engine:
        dispose=AsyncMock()
    db,engine=Db(),Engine()
    async def session(): return db,engine
    class Recorder:
        def __init__(self,*_args): self.seen=[]
        async def evaluate_and_record_supplier_review(self,supplier_id):
            if supplier_id==supplier_ids[1]: raise RuntimeError("isolated failure")
    monkeypatch.setattr(supplier_policy_review_tasks,"create_worker_session",session)
    monkeypatch.setattr(supplier_policy_review_tasks,"SupplierPolicyReviewStateService",Recorder)
    result=await supplier_policy_review_tasks._evaluate_supplier_policy_reviews(batch_size=1)
    assert result == {"evaluated_count":2,"failed_count":1,"failed_supplier_ids":[str(supplier_ids[1])]}
    db.rollback.assert_awaited_once();engine.dispose.assert_awaited_once()
