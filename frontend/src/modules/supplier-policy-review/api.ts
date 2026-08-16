import { apiClient } from "../../lib/api";
import type { ReviewItem,ReviewPage,ReviewSettings,ReviewTransition } from "./types";
import type { Paginated } from "../research-common/types";

export const fetchReviewSettings=()=>apiClient.get<ReviewSettings>("/supplier-policy-review/settings");
export const updateReviewSettings=(body:Omit<ReviewSettings,"id"|"user_id">)=>apiClient.put<ReviewSettings,typeof body>("/supplier-policy-review/settings",body);
export const fetchReviewQueue=(query:string)=>apiClient.get<ReviewPage>(`/supplier-policy-review${query?`?${query}`:""}`);
export const fetchSupplierReview=(id:string)=>apiClient.get<ReviewItem>(`/supplier-policy-review/${id}`);
export const fetchReviewTransitions=(id:string)=>apiClient.get<Paginated<ReviewTransition>>(`/supplier-policy-review/${id}/transitions?page_size=20`);
