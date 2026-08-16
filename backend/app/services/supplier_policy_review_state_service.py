from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.notification_outbox import NotificationOutbox
from app.models.supplier import Supplier
from app.models.supplier_policy_review_state import SupplierPolicyReviewState
from app.models.supplier_policy_review_transition import SupplierPolicyReviewTransition


class SupplierPolicyReviewStateService:
    EVENT_TYPE = "supplier_policy_review_changed"
    RESOURCE_TYPE = "supplier"

    def __init__(self, db, review_service):
        self.db = db
        self.review_service = review_service

    async def evaluate_and_record_supplier_review(self, supplier_id, *, retry_initial_conflict=True):
        state = await self.db.scalar(
            select(SupplierPolicyReviewState)
            .where(SupplierPolicyReviewState.supplier_id == supplier_id)
            .with_for_update()
        )
        supplier = await self.db.get(Supplier, supplier_id)
        if supplier is None:
            return None
        settings = await self.review_service.settings(supplier.owner_user_id)
        review = await self.review_service.evaluate(supplier, settings)
        now = datetime.now(timezone.utc)
        type_statuses = {key: value["review_status"] for key, value in review["types"].items()}
        issue_types = sorted(review["issue_types"])
        initial = state is None
        if state is not None and state.overall_status == review["overall_status"] and state.type_statuses == type_statuses:
            state.evaluated_at = now
            await self.db.commit()
            return {"state": state, "transition": None, "outbox": None}

        previous_status = state.overall_status if state else None
        previous_types = state.type_statuses if state else {}
        changed_types = sorted(key for key in type_statuses if previous_types.get(key) != type_statuses[key])
        version = state.version + 1 if state else 1
        if state is None:
            state = SupplierPolicyReviewState(
                supplier_id=supplier.id, owner_user_id=supplier.owner_user_id,
                overall_status=review["overall_status"], issue_types=issue_types,
                type_statuses=type_statuses, version=version, evaluated_at=now,
            )
            self.db.add(state)
        else:
            state.overall_status = review["overall_status"]
            state.issue_types = issue_types
            state.type_statuses = type_statuses
            state.version = version
            state.evaluated_at = now

        transition_id = uuid4()
        transition = SupplierPolicyReviewTransition(
            id=transition_id, supplier_id=supplier.id, owner_user_id=supplier.owner_user_id,
            state_version=version, from_status=previous_status, to_status=review["overall_status"],
            changed_evidence_types=changed_types,
            reason_summary=self._reason(previous_status, review["overall_status"], changed_types),
            occurred_at=now,
        )
        self.db.add(transition)
        outbox = None
        if not initial:
            # Establish the transition FK target before the Outbox INSERT while
            # keeping both records inside the same transaction and commit.
            await self.db.flush()
            payload = {
                "supplier_id": str(supplier.id), "supplier_name": supplier.name,
                "from_status": previous_status, "to_status": review["overall_status"],
                "changed_evidence_types": changed_types, "occurred_at": now.isoformat(),
            }
            outbox = NotificationOutbox(
                owner_user_id=supplier.owner_user_id, transition_id=transition_id,
                event_type=self.EVENT_TYPE, resource_type=self.RESOURCE_TYPE,
                resource_id=supplier.id, payload=payload,
                dedupe_key=f"supplier-policy-review:{transition_id}", status="pending", available_at=now,
            )
            self.db.add(outbox)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            if initial and retry_initial_conflict:
                return await self.evaluate_and_record_supplier_review(supplier_id, retry_initial_conflict=False)
            raise
        except Exception:
            await self.db.rollback()
            raise
        await self.db.refresh(state)
        return {"state": state, "transition": transition, "outbox": outbox}

    @staticmethod
    def _reason(from_status, to_status, changed_types):
        before = from_status or "not_evaluated"
        types = ", ".join(changed_types) if changed_types else "overall status"
        return f"Review changed from {before} to {to_status}; changed types: {types}."
