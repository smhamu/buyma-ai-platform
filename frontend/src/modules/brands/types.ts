import type { Paginated, SortOrder } from "../research-common/types";

export type LuxuryTier = "ultra_luxury" | "luxury" | "premium";
export type PurchasePolicy = "normal" | "limited" | "category_limited" | "boutique_only" | "research_only" | "unknown";
export type Brand = { id: string; brand_code: string; brand_name: string; luxury_tier: LuxuryTier; official_site_url: string | null; online_purchase_policy: PurchasePolicy; purchase_restriction_notes: string | null; is_research_enabled: boolean; is_active: boolean; created_at: string; updated_at: string };
export type BrandSummary = Pick<Brand, "id" | "brand_code" | "brand_name">;
export type BrandInput = Omit<Brand, "id" | "created_at" | "updated_at">;
export type BrandQuery = { q?: string; luxury_tier?: string; online_purchase_policy?: string; is_research_enabled?: boolean; is_active?: boolean; page?: number; page_size?: number; sort_by?: "brand_name" | "luxury_tier" | "created_at" | "updated_at"; sort_order?: SortOrder };
export type BrandPage = Paginated<Brand>;
