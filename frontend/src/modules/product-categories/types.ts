import type { PurchasePolicy } from "../brands/types";

export type ProductCategory = { id:string; category_code:string; category_name:string; is_active:boolean };
export type CategoryPolicy = { id:string; brand_id:string; category_id:string; category:ProductCategory; online_purchase_policy:PurchasePolicy; research_enabled:boolean; policy_notes:string|null; checked_at:string|null; created_at:string; updated_at:string };
export type CategoryPolicyInput = { category_id:string; online_purchase_policy:PurchasePolicy; research_enabled:boolean; policy_notes:string|null; checked_at:string|null };
export type ResolvedPolicy = { policy:PurchasePolicy; research_enabled:boolean; source:"category_override"|"brand_default" };
