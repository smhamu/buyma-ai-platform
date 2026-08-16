from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status as http_status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.common.exceptions import AppException, NotFoundException
from app.common.responses import success_response
from app.core.config import settings
from app.core.database import get_db
from app.models.notification_delivery import NotificationDelivery
from app.models.user import User
from app.schemas.notification import NotificationDeliveryResponse, NotificationDeliveryStatsResponse
from app.schemas.pagination import PaginatedResponse
from app.services.notification_delivery_service import NotificationDeliveryConsumerService

router = APIRouter(prefix="/notification-deliveries", tags=["Notification Deliveries"])


def ownership(current_user):
    return [] if current_user.role == "admin" else [NotificationDelivery.user_id == current_user.id]


@router.get("")
async def list_deliveries(
    status: Literal["pending","processing","delivered","failed","cancelled"] | None = None,
    channel_type: Literal["slack","email","line"] | None = None,
    event_type: str | None = None, resource_id: UUID | None = None,
    created_from: datetime | None = None, created_to: datetime | None = None,
    page: int = Query(1,ge=1), page_size: int = Query(20,ge=1,le=100),
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters=ownership(current_user)
    if status:filters.append(NotificationDelivery.status==status)
    if channel_type:filters.append(NotificationDelivery.channel_type==channel_type)
    if event_type:filters.append(NotificationDelivery.event_type==event_type)
    if resource_id:filters.append(NotificationDelivery.resource_id==resource_id)
    if created_from:filters.append(NotificationDelivery.created_at>=created_from)
    if created_to:filters.append(NotificationDelivery.created_at<=created_to)
    total=int(await db.scalar(select(func.count(NotificationDelivery.id)).where(*filters)) or 0)
    rows=await db.execute(select(NotificationDelivery).where(*filters).order_by(desc(NotificationDelivery.created_at)).offset((page-1)*page_size).limit(page_size))
    data=PaginatedResponse[NotificationDeliveryResponse](
        items=[NotificationDeliveryResponse.model_validate(x) for x in rows.scalars()],page=page,page_size=page_size,total=total,total_pages=(total+page_size-1)//page_size,
    )
    return success_response(data=data,message="Notification deliveries fetched successfully.")


@router.get("/stats")
async def delivery_stats(
    channel_type: Literal["slack","email","line"] | None = None,
    db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user),
):
    filters=ownership(current_user)
    if channel_type:filters.append(NotificationDelivery.channel_type==channel_type)
    grouped=await db.execute(select(NotificationDelivery.status,func.count(NotificationDelivery.id)).where(*filters).group_by(NotificationDelivery.status))
    counts=dict(grouped.all());oldest=await db.scalar(select(func.min(NotificationDelivery.available_at)).where(*filters,NotificationDelivery.status=="pending"))
    now=datetime.now(oldest.tzinfo) if oldest and oldest.tzinfo else datetime.now()
    data=NotificationDeliveryStatsResponse(
        pending_count=counts.get("pending",0),processing_count=counts.get("processing",0),delivered_count=counts.get("delivered",0),failed_count=counts.get("failed",0),cancelled_count=counts.get("cancelled",0),oldest_pending_at=oldest,oldest_pending_age_seconds=max(0,int((now-oldest).total_seconds())) if oldest else None,
    )
    return success_response(data=data,message="Notification delivery stats fetched successfully.")


@router.post("/{delivery_id}/retry")
async def retry_delivery(
    delivery_id: UUID,db: AsyncSession=Depends(get_db),current_user: User=Depends(get_current_user),
):
    service=NotificationDeliveryConsumerService(db,None,max_attempts=settings.notification_outbox_max_attempts)
    try:item=await service.retry_failed(delivery_id,owner_user_id=None if current_user.role=="admin" else current_user.id)
    except ValueError:
        raise AppException(http_status.HTTP_409_CONFLICT,"DELIVERY_NOT_RETRYABLE","Only failed deliveries can be retried.")
    if item is None:raise NotFoundException("notification delivery")
    return success_response(data=NotificationDeliveryResponse.model_validate(item),message="Notification delivery queued for retry.")
