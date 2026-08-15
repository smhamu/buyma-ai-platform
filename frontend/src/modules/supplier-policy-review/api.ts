import { apiClient } from "../../lib/api";
import type { ReviewItem,ReviewPage,ReviewSettings } from "./types";

export const fetchReviewSettings=()=>apiClient.get<ReviewSettings>("/supplier-policy-review/settings");
export const updateReviewSettings=(body:Omit<ReviewSettings,"id"|"user_id">)=>apiClient.put<ReviewSettings,typeof body>("/supplier-policy-review/settings",body);
export const fetchReviewQueue=(query:string)=>apiClient.get<ReviewPage>(`/supplier-policy-review${query?`?${query}`:""}`);
export const fetchSupplierReview=(id:string)=>apiClient.get<ReviewItem>(`/supplier-policy-review/${id}`);
