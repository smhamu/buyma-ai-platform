from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.responses import success_response
from app.core.database import get_db
from app.models.notification_outbox import NotificationOutbox
from app.models.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.supplier_policy_review import NotificationOutboxResponse

router = APIRouter(prefix="/notification-outbox", tags=["Notification Outbox"])


@router.get("")
async def list_notification_outbox(
    status: Literal["pending", "processing", "delivered", "failed", "cancelled"] | None = None,
    event_type: Literal["supplier_policy_review_changed"] | None = None,
    resource_id: UUID | None = None, created_from: datetime | None = None,
    created_to: datetime | None = None, page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = [NotificationOutbox.owner_user_id == current_user.id]
    if status: filters.append(NotificationOutbox.status == status)
    if event_type: filters.append(NotificationOutbox.event_type == event_type)
    if resource_id: filters.append(NotificationOutbox.resource_id == resource_id)
    if created_from: filters.append(NotificationOutbox.created_at >= created_from)
    if created_to: filters.append(NotificationOutbox.created_at <= created_to)
    total = int((await db.scalar(select(func.count(NotificationOutbox.id)).where(*filters))) or 0)
    rows = await db.execute(
        select(NotificationOutbox).where(*filters)
        .order_by(desc(NotificationOutbox.created_at), desc(NotificationOutbox.id))
        .offset((page - 1) * page_size).limit(page_size)
    )
    data = PaginatedResponse[NotificationOutboxResponse](
        items=[NotificationOutboxResponse.model_validate(item) for item in rows.scalars()],
        page=page, page_size=page_size, total=total,
        total_pages=(total + page_size - 1) // page_size,
    )
    return success_response(data=data, message="Notification outbox events fetched successfully.")
