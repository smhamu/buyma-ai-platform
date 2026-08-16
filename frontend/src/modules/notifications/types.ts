export type NotificationEventType = "supplier_policy_review_changed";
export type SlackChannelSetting = {
  channel_type: "slack";
  enabled: boolean;
  configured: boolean;
  destination_label: string;
  subscribed_event_types: NotificationEventType[];
};
export type SlackChannelUpdate = {
  enabled: boolean;
  webhook_url?: string;
  destination_label: string;
  subscribed_event_types: NotificationEventType[];
};
export type NotificationDelivery = {
  id: string; channel_type: string; event_type: string;
  status: string; created_at: string; delivered_at: string | null;
};
export type DeliveryPage = {items:NotificationDelivery[];page:number;page_size:number;total:number;total_pages:number};
