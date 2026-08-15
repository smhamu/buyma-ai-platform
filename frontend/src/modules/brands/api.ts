import { apiClient } from "../../lib/api";
import type { Brand, BrandInput, BrandPage, BrandQuery } from "./types";

const queryString = (query: Record<string, unknown>) => { const p = new URLSearchParams(); Object.entries(query).forEach(([k,v]) => { if (v !== undefined && v !== "") p.set(k, String(v)); }); return p.toString(); };
export const fetchBrands = (query: BrandQuery = {}) => apiClient.get<BrandPage>(`/brands?${queryString(query)}`);
export const fetchBrand = (id: string) => apiClient.get<Brand>(`/brands/${id}`);
export const createBrand = (body: BrandInput) => apiClient.post<Brand, BrandInput>("/brands", body);
export const updateBrand = (id: string, body: Partial<BrandInput>) => apiClient.put<Brand, Partial<BrandInput>>(`/brands/${id}`, body);
export const deleteBrand = (id: string) => apiClient.delete<{ deleted: boolean }>(`/brands/${id}`);
