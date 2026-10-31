import { apiClient } from "../../lib/api";
import type { RakutenTokenSetting, RakutenTokenUpdate } from "./types";

const path = "/integration-settings/rakuten";

export const fetchRakutenSetting = () => apiClient.get<RakutenTokenSetting>(path);
export const saveRakutenToken = (body: RakutenTokenUpdate) =>
  apiClient.put<RakutenTokenSetting, RakutenTokenUpdate>(path, body);
export const removeRakutenToken = () => apiClient.delete<RakutenTokenSetting>(path);
