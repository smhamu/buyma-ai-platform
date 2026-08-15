import type { BrandSummary } from "../brands/types";
import type { Paginated, SortOrder } from "../research-common/types";

export type Supplier = { id: string; owner_user_id: string; name: string; country_code: string; website_url: string; supplier_type: string; default_currency: string; ships_to_japan: boolean; vat_policy: string; vat_rate: string | null; japan_shipping_cost: string | null; buyma_allowed_status: string; buyma_status_checked_at: string | null; research_status: string; notes: string | null; is_active: boolean; brands: BrandSummary[]; created_at: string; updated_at: string };
export type SupplierInput = Omit<Supplier, "id" | "owner_user_id" | "brands" | "created_at" | "updated_at"> & { brand_ids: string[] };
export type SupplierQuery = { country?: string; supplier_type?: string; ships_to_japan?: boolean; buyma_allowed_status?: string; research_status?: string; is_active?: boolean; page?: number; page_size?: number; sort_by?: "name" | "country_code" | "created_at" | "updated_at"; sort_order?: SortOrder };
export type SupplierPage = Paginated<Supplier>;
