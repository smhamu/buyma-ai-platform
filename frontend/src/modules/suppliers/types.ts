import type { BrandSummary } from "../brands/types";
import type { Paginated, SortOrder } from "../research-common/types";

export type Supplier = { id: string; owner_user_id: string; name: string; country_code: string; website_url: string; supplier_type: string; default_currency: string; ships_to_japan: boolean; vat_policy: string; vat_rate: string | null; japan_shipping_cost: string | null; buyma_allowed_status: string; buyma_status_checked_at: string | null; research_status: string; notes: string | null; is_active: boolean; brands: BrandSummary[]; ingestion_source_type:string; automated_fetch_enabled:boolean; terms_status:string; robots_status:string; terms_checked_at:string|null; robots_checked_at:string|null; official_api_available:boolean; research_policy_notes:string|null; parser_key:string|null; request_interval_seconds:number|null; last_fetch_at:string|null; created_at: string; updated_at: string };
export type SupplierInput = Omit<Supplier, "id" | "owner_user_id" | "brands" | "created_at" | "updated_at"> & { brand_ids: string[] };
export type SupplierQuery = { country?: string; supplier_type?: string; ships_to_japan?: boolean; buyma_allowed_status?: string; research_status?: string; is_active?: boolean; page?: number; page_size?: number; sort_by?: "name" | "country_code" | "created_at" | "updated_at"; sort_order?: SortOrder };
export type SupplierPage = Paginated<Supplier>;

export type EvidenceType = "terms" | "robots" | "vat" | "shipping" | "official_api" | "buyma" | "ingestion" | "resale_restriction" | "other";
export type EvidenceResult = "allowed" | "restricted" | "prohibited" | "disallowed" | "supported" | "unsupported" | "confirmed" | "unconfirmed" | "unknown" | "unchecked" | "caution" | "included" | "excluded_for_export" | "not_refunded" | "manual" | "url_manual" | "csv" | "official_api" | "structured_data" | "html_parser" | "disabled";
export type SupplierPolicyEvidence = { id:string; supplier_id:string; owner_user_id:string; evidence_type:EvidenceType; result:EvidenceResult; source_url:string|null; source_title:string|null; source_excerpt:string|null; evidence_notes:string; checked_at:string; checked_by_user_id:string; checked_by_username:string; policy_snapshot:Record<string,unknown>; created_at:string; updated_at:string };
export type SupplierPolicyEvidenceInput = Pick<SupplierPolicyEvidence,"evidence_type"|"result"|"source_url"|"source_title"|"source_excerpt"|"evidence_notes"|"checked_at">;
export type SupplierPolicyEvidencePage = Paginated<SupplierPolicyEvidence>;
export type PolicyEvidenceSummaryItem = { current:string|boolean; latest_evidence:string|null; evidence_id:string|null; checked_at:string|null; age_days:number|null; is_stale:boolean|null; consistent:boolean|null };
export type PolicyEvidenceSummary = Record<"terms"|"robots"|"vat"|"shipping"|"official_api"|"buyma",PolicyEvidenceSummaryItem>;
