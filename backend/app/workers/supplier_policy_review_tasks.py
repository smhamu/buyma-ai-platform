import asyncio

from sqlalchemy import select

from app.models.supplier import Supplier
from app.models.product_category import BrandCategoryPolicy  # noqa: F401 - register ORM relationship
from app.models.user import User  # noqa: F401 - register ORM relationship
from app.repositories.brand_repository import BrandRepository
from app.repositories.supplier_policy_evidence_repository import SupplierPolicyEvidenceRepository
from app.repositories.supplier_repository import SupplierRepository
from app.services.supplier_policy_evidence_service import SupplierPolicyEvidenceService
from app.services.supplier_policy_review_service import SupplierPolicyReviewService
from app.services.supplier_policy_review_state_service import SupplierPolicyReviewStateService
from app.services.supplier_service import SupplierService
from app.workers.celery_app import celery_app
from app.workers.database import create_worker_session


async def _evaluate_supplier_policy_reviews(batch_size=100):
    db, engine = await create_worker_session()
    evaluated = 0
    failed = []
    try:
        async with db:
            supplier_ids = list((await db.scalars(select(Supplier.id).where(Supplier.is_active.is_(True)).order_by(Supplier.id))).all())
            suppliers = SupplierService(SupplierRepository(db), BrandRepository(db))
            evidence = SupplierPolicyEvidenceService(SupplierPolicyEvidenceRepository(db), suppliers)
            recorder = SupplierPolicyReviewStateService(db, SupplierPolicyReviewService(db, evidence))
            for offset in range(0, len(supplier_ids), batch_size):
                for supplier_id in supplier_ids[offset:offset + batch_size]:
                    try:
                        await recorder.evaluate_and_record_supplier_review(supplier_id)
                        evaluated += 1
                    except Exception:
                        await db.rollback()
                        failed.append(str(supplier_id))
        return {"evaluated_count": evaluated, "failed_count": len(failed), "failed_supplier_ids": failed}
    finally:
        await engine.dispose()


@celery_app.task(name="supplier_policy_review.evaluate", autoretry_for=(), max_retries=0)
def evaluate_supplier_policy_reviews_task():
    return asyncio.run(_evaluate_supplier_policy_reviews())
