import type { Paginated } from "../research-common/types";

export type ResearchSource = {
  id:string; supplier_id:string; brand_id:string|null; category_id:string|null; source_type:string;
  source_url:string; external_product_id:string|null; raw_title:string|null;
  raw_price:string|null; raw_currency:string|null; normalized_title:string|null;
  normalized_price:string|null; normalized_currency:string|null;
  normalized_availability:string|null; processing_status:string;
  purchase_restriction:string|null;
  candidate_id:string|null; created_at:string;
};
export type ResearchSourcePage = Paginated<ResearchSource>;
export type CsvImportResult = {success_count:number;failed_count:number;duplicate_count:number;rows:Array<{row:number;status:string;source_id:string|null;message:string|null}>};
