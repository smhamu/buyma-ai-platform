import { apiClient } from "../../lib/api";
import type { Candidate } from "../product-research/types";
import type {
  CsvImportResult,
  ResearchSource,
  ResearchSourcePage,
} from "./types";

export const fetchResearchSources = (query = "") =>
  apiClient.get<ResearchSourcePage>(`/research-ingestion?${query}`);
export const registerResearchUrl = (supplier_id: string, url: string, category_id: string|null = null) =>
  apiClient.post<ResearchSource, { supplier_id: string; url: string; category_id:string|null }>(
    "/research-ingestion/url",
    { supplier_id, url, category_id },
  );
export const importResearchCsv = (file: File) => {
  const body = new FormData();
  body.append("file", file);
  return apiClient.postForm<CsvImportResult>("/research-ingestion/csv", body);
};
export const createCandidateFromSource = (
  id: string,
  body: { exchange_rate: string; buyma_price: string; buyma_fee_rate: string },
) =>
  apiClient.post<Candidate, typeof body>(
    `/research-ingestion/${id}/create-candidate`,
    body,
  );
export const deleteResearchSource = (id: string) =>
  apiClient.delete<{ deleted: boolean }>(`/research-ingestion/${id}`);
