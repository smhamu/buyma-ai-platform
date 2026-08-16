import { apiClient } from "../../lib/api";
import type { DeliveryPage, SlackChannelSetting, SlackChannelUpdate } from "./types";

export const fetchSlackSetting = () => apiClient.get<SlackChannelSetting>("/notification-channels/slack");
export const saveSlackSetting = (body: SlackChannelUpdate) => apiClient.put<SlackChannelSetting, SlackChannelUpdate>("/notification-channels/slack", body);
export const removeSlackSetting = () => apiClient.delete<SlackChannelSetting>("/notification-channels/slack");
export const fetchRecentDeliveries = () => apiClient.get<DeliveryPage>("/notification-deliveries?channel_type=slack&page_size=5");
