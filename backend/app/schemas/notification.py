from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

NotificationEventType = Literal["supplier_policy_review_changed"]
DeliveryStatus = Literal["pending", "processing", "delivered", "failed", "cancelled"]


class SlackChannelUpdate(BaseModel):
    enabled: bool
    webhook_url: str | None = None
    destination_label: str = Field(default="Slack", min_length=1, max_length=100)
    subscribed_event_types: list[NotificationEventType] = Field(default_factory=list)

    @field_validator("subscribed_event_types")
    @classmethod
    def unique_events(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("subscribed_event_types must not contain duplicates.")
        return value


class NotificationChannelResponse(BaseModel):
    channel_type: Literal["slack"] = "slack"
    enabled: bool = False
    configured: bool = False
    destination_label: str = "Slack"
    subscribed_event_types: list[NotificationEventType] = Field(default_factory=list)


class NotificationDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    outbox_id: UUID
    channel_type: Literal["slack", "email", "line"]
    event_type: str
    resource_id: UUID
    status: DeliveryStatus
    available_at: datetime
    processing_started_at: datetime | None
    delivered_at: datetime | None
    attempt_count: int
    last_error: str | None
    provider_status_code: int | None
    created_at: datetime
    updated_at: datetime


class NotificationDeliveryStatsResponse(BaseModel):
    pending_count: int
    processing_count: int
    delivered_count: int
    failed_count: int
    cancelled_count: int
    oldest_pending_at: datetime | None
    oldest_pending_age_seconds: int | None
