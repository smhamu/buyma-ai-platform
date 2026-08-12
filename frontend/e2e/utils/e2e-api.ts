import { request, type APIRequestContext, expect } from "@playwright/test";

export type E2ECredentials = {
  email: string;
  password: string;
  username: string;
};

type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

type KnowledgeBaseResponse = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
};

type ApiEnvelope<T> = {
  success: true;
  message: string;
  data: T;
};

const apiBaseURL = process.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function uniqueValue(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export async function createApiContext() {
  return request.newContext({
    baseURL: apiBaseURL,
    extraHTTPHeaders: {
      Accept: "application/json",
    },
  });
}

export async function ensureUser(
  api: APIRequestContext,
  preferredEmail: string | undefined,
  preferredPassword: string | undefined,
  prefix: string,
): Promise<E2ECredentials> {
  if (preferredEmail && preferredPassword) {
    return {
      email: preferredEmail,
      password: preferredPassword,
      username: preferredEmail.split("@")[0],
    };
  }

  const email = `${uniqueValue(prefix)}@example.com`;
  const password = `Pw!${Date.now()}Aa1`;
  const username = uniqueValue(prefix);

  const registerResponse = await api.post("/auth/register", {
    data: { email, password, username },
  });

  expect(registerResponse.ok()).toBeTruthy();

  return { email, password, username };
}

export async function loginByApi(api: APIRequestContext, credentials: E2ECredentials) {
  const response = await api.post("/auth/login", {
    data: {
      email: credentials.email,
      password: credentials.password,
    },
  });

  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as ApiEnvelope<LoginResponse>;
  return payload.data;
}

export async function createKnowledgeBase(
  api: APIRequestContext,
  accessToken: string,
  name: string,
) {
  const response = await api.post("/knowledge-bases", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    data: {
      name,
      description: `${name} description`,
      is_active: true,
    },
  });

  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as ApiEnvelope<KnowledgeBaseResponse>;
  return payload.data;
}

export async function deleteKnowledgeBase(
  api: APIRequestContext,
  accessToken: string,
  knowledgeBaseId: string,
) {
  const response = await api.delete(`/knowledge-bases/${knowledgeBaseId}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  expect(response.ok()).toBeTruthy();
}
