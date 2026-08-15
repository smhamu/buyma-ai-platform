import type { APIRequestContext } from "@playwright/test";

type Envelope<T> = { success: true; data: T };
export type ResearchIds = { candidateId?: string; supplierId?: string; brandId?: string };

const auth = (token: string) => ({ Authorization: `Bearer ${token}` });

export async function findBrand(api: APIRequestContext, token: string, code: string) {
  const response = await api.get(`/brands?q=${encodeURIComponent(code)}&page_size=100`, { headers: auth(token) });
  if (!response.ok()) throw new Error("Failed to find E2E brand.");
  const payload = await response.json() as Envelope<{ items: Array<{ id: string; brand_code: string }> }>;
  return payload.data.items.find(item => item.brand_code === code);
}

export async function findSupplier(api: APIRequestContext, token: string, name: string) {
  const response = await api.get("/suppliers?page_size=100&is_active=true", { headers: auth(token) });
  if (!response.ok()) throw new Error("Failed to find E2E supplier.");
  const payload = await response.json() as Envelope<{
    items: Array<{
      id: string;
      name: string;
      brands: Array<{ id: string; brand_code: string; brand_name: string }>;
    }>;
  }>;
  return payload.data.items.find(item => item.name === name);
}

export async function updateSupplierStatus(api: APIRequestContext, token: string, id: string, status: string) {
  const response = await api.put(`/suppliers/${id}`, { headers: auth(token), data: { buyma_allowed_status: status } });
  if (!response.ok()) throw new Error("Failed to update E2E supplier status.");
}

export async function cleanupResearchData(api: APIRequestContext, token: string, ids: ResearchIds) {
  for (const [path, id] of [["product-research-candidates", ids.candidateId], ["suppliers", ids.supplierId], ["brands", ids.brandId]] as const) {
    if (!id) continue;
    try { await api.delete(`/${path}/${id}`, { headers: auth(token) }); } catch { /* cleanup is best effort */ }
  }
}
