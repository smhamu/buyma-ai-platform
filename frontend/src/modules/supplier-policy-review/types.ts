import type { Paginated } from "../research-common/types";

export type ReviewEvidenceType="terms"|"robots"|"vat"|"shipping"|"official_api"|"buyma";
export type ReviewStatus="up_to_date"|"review_due"|"inconsistent"|"no_evidence";
export type ReviewSettings={
  id?:string;user_id:string;required_evidence_types:ReviewEvidenceType[];
  terms_max_age_days:number|null;robots_max_age_days:number|null;vat_max_age_days:number|null;
  shipping_max_age_days:number|null;official_api_max_age_days:number|null;buyma_max_age_days:number|null;
};
export type TypeReview={current:string;latest_evidence:string|null;checked_at:string|null;age_days:number|null;max_age_days:number|null;consistent:boolean|null;is_stale:boolean|null;review_status:ReviewStatus};
export type ReviewItem={supplier_id:string;supplier_name:string;country_code:string;supplier_type:string;brand_names:string[];updated_at:string;overall_status:ReviewStatus;priority:"critical"|"high"|"medium"|"normal";issue_types:ReviewEvidenceType[];oldest_evidence_at:string|null;types:Record<ReviewEvidenceType,TypeReview>};
export type ReviewPage=Paginated<ReviewItem>&{summary:Record<ReviewStatus,number>};
export type ReviewTransition={id:string;supplier_id:string;state_version:number;from_status:ReviewStatus|null;to_status:ReviewStatus;changed_evidence_types:ReviewEvidenceType[];reason_summary:string;occurred_at:string;created_at:string};
