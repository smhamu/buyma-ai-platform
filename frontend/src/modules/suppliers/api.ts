import { apiClient } from "../../lib/api";
import type { Supplier, SupplierInput, SupplierPage, SupplierQuery } from "./types";

const qs = (q: Record<string, unknown>) => { const p=new URLSearchParams(); Object.entries(q).forEach(([k,v])=>{if(v!==undefined&&v!=="")p.set(k,String(v));}); return p.toString(); };
export const fetchSuppliers = (q: SupplierQuery = {}) => apiClient.get<SupplierPage>(`/suppliers?${qs(q)}`);
export const fetchSupplier = (id:string) => apiClient.get<Supplier>(`/suppliers/${id}`);
export const createSupplier = (body:SupplierInput) => apiClient.post<Supplier,SupplierInput>("/suppliers",body);
export const updateSupplier = (id:string,body:Partial<SupplierInput>) => apiClient.put<Supplier,Partial<SupplierInput>>(`/suppliers/${id}`,body);
export const deleteSupplier = (id:string) => apiClient.delete<{deleted:boolean}>(`/suppliers/${id}`);
