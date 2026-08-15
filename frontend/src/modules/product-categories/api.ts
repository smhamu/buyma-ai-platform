import { apiClient } from "../../lib/api";
import type { CategoryPolicy, CategoryPolicyInput, ProductCategory, ResolvedPolicy } from "./types";

export const fetchProductCategories=()=>apiClient.get<ProductCategory[]>("/product-categories");
export const fetchCategoryPolicies=(brandId:string)=>apiClient.get<CategoryPolicy[]>(`/brands/${brandId}/category-policies`);
export const resolvePurchasePolicy=(brandId:string,categoryId:string|null)=>apiClient.get<ResolvedPolicy>(`/brands/${brandId}/resolved-purchase-policy${categoryId?`?category_id=${categoryId}`:""}`);
export const createCategoryPolicy=(brandId:string,body:CategoryPolicyInput)=>apiClient.post<CategoryPolicy,CategoryPolicyInput>(`/brands/${brandId}/category-policies`,body);
export const updateCategoryPolicy=(brandId:string,id:string,body:Partial<CategoryPolicyInput>)=>apiClient.put<CategoryPolicy,Partial<CategoryPolicyInput>>(`/brands/${brandId}/category-policies/${id}`,body);
export const deleteCategoryPolicy=(brandId:string,id:string)=>apiClient.delete<{deleted:boolean}>(`/brands/${brandId}/category-policies/${id}`);
