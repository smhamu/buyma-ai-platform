import { expect, type APIRequestContext } from "@playwright/test";

type Envelope<T> = { success: true; data: T };
const auth = (token: string) => ({ Authorization: `Bearer ${token}` });

export type IngestionIds = {
  brandId?: string;
  supplierId?: string;
  candidateId?: string;
  sourceIds: string[];
};

export async function createIngestionBrand(
  api: APIRequestContext,
  token: string,
  code: string,
  name: string,
) {
  const response = await api.post("/brands", {
    headers: auth(token),
    data: {
      brand_code: code,
      brand_name: name,
      luxury_tier: "luxury",
      online_purchase_policy: "normal",
      is_research_enabled: true,
      is_active: true,
    },
  });
  expect(response.ok()).toBeTruthy();
  return ((await response.json()) as Envelope<{ id: string }>).data;
}

export async function createIngestionSupplier(
  api: APIRequestContext,
  token: string,
  brandId: string,
  name: string,
  websiteUrl: string,
) {
  const response = await api.post("/suppliers", {
    headers: auth(token),
    data: {
      name,
      country_code: "FR",
      website_url: websiteUrl,
      supplier_type: "authorized_retailer",
      default_currency: "EUR",
      brand_ids: [brandId],
      ships_to_japan: true,
      vat_policy: "excluded_for_export",
      vat_rate: "0.20",
      buyma_allowed_status: "allowed",
      research_status: "approved",
      is_active: true,
      ingestion_source_type: "url_manual",
      automated_fetch_enabled: false,
      terms_status: "allowed",
      robots_status: "allowed",
      official_api_available: false,
    },
  });
  expect(response.ok()).toBeTruthy();
  return (
    (await response.json()) as Envelope<{
      id: string;
      ingestion_source_type: string;
      automated_fetch_enabled: boolean;
      terms_status: string;
      robots_status: string;
      ships_to_japan: boolean;
      country_code: string;
      default_currency: string;
    }>
  ).data;
}

export async function findSources(
  api: APIRequestContext,
  token: string,
  q: string,
) {
  const response = await api.get(
    `/research-ingestion?q=${encodeURIComponent(q)}&page_size=100`,
    { headers: auth(token) },
  );
  expect(response.ok()).toBeTruthy();
  return (
    (await response.json()) as Envelope<{
      items: Array<{
        id: string;
        candidate_id: string | null;
        processing_status: string;
        source_url: string;
      }>;
    }>
  ).data.items;
}

export async function getSource(
  api: APIRequestContext,
  token: string,
  id: string,
) {
  const response = await api.get(`/research-ingestion/${id}`, {
    headers: auth(token),
  });
  expect(response.ok()).toBeTruthy();
  return (
    (await response.json()) as Envelope<{
      id: string;
      candidate_id: string | null;
      processing_status: string;
      source_type: string;
      supplier_id: string;
      brand_id: string | null;
    }>
  ).data;
}

export async function getCandidate(
  api: APIRequestContext,
  token: string,
  id: string,
) {
  const response = await api.get(`/product-research-candidates/${id}`, {
    headers: auth(token),
  });
  expect(response.ok()).toBeTruthy();
  return (
    (await response.json()) as Envelope<{
      id: string;
      source_product_id: string | null;
      brand_id: string;
      supplier_id: string;
    }>
  ).data;
}

export async function deleteConvertedSource(
  api: APIRequestContext,
  token: string,
  id: string,
) {
  return api.delete(`/research-ingestion/${id}`, { headers: auth(token) });
}

export async function cleanupIngestion(
  api: APIRequestContext,
  token: string,
  ids: IngestionIds,
) {
  if (ids.candidateId) {
    try {
      await api.delete(`/product-research-candidates/${ids.candidateId}`, {
        headers: auth(token),
      });
    } catch {
      /* best effort */
    }
  }
  for (const id of ids.sourceIds) {
    try {
      await api.delete(`/research-ingestion/${id}`, { headers: auth(token) });
    } catch {
      /* best effort */
    }
  }
  for (const [path, id] of [
    ["suppliers", ids.supplierId],
    ["brands", ids.brandId],
  ] as const) {
    if (!id) continue;
    try {
      await api.delete(`/${path}/${id}`, { headers: auth(token) });
    } catch {
      /* best effort */
    }
  }
}
