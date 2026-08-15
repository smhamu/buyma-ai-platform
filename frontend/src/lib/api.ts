import { API_BASE_URL } from "./config";

export type ApiSuccessResponse<T> = {
  success: true;
  message: string;
  data: T;
};

export type ApiErrorDetail = {
  field?: string | null;
  message: string;
  type?: string | null;
};

export type ApiErrorResponse = {
  success: false;
  code: string;
  message: string;
  errors?: ApiErrorDetail[];
};

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly errors?: ApiErrorDetail[];

  constructor(
    status: number,
    code: string,
    message: string,
    errors?: ApiErrorDetail[],
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.errors = errors;
  }
}

type TokenProvider = () => string | null;
type RefreshHandler = () => Promise<string | null>;
type UnauthorizedHandler = () => void;

let accessTokenProvider: TokenProvider = () => null;
let refreshHandler: RefreshHandler = async () => null;
let unauthorizedHandler: UnauthorizedHandler = () => undefined;

export function configureApiClient(config: {
  getAccessToken: TokenProvider;
  refreshAccessToken: RefreshHandler;
  onUnauthorized: UnauthorizedHandler;
}) {
  accessTokenProvider = config.getAccessToken;
  refreshHandler = config.refreshAccessToken;
  unauthorizedHandler = config.onUnauthorized;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  retryOnUnauthorized = true,
): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  const token = accessTokenProvider();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (response.status === 401 && retryOnUnauthorized) {
    const refreshedToken = await refreshHandler();
    if (refreshedToken) {
      return request<T>(path, init, false);
    }
    unauthorizedHandler();
  }

  const payload = (await response.json()) as
    | ApiSuccessResponse<T>
    | ApiErrorResponse;

  if (!response.ok || payload.success === false) {
    const error = payload as ApiErrorResponse;
    if (response.status === 401) {
      unauthorizedHandler();
    }
    throw new ApiClientError(
      response.status,
      error.code || "UNKNOWN_ERROR",
      error.message || "Request failed.",
      error.errors,
    );
  }

  return payload.data;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T, B>(path: string, body: B) =>
    request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  postForm: <T>(path: string, body: FormData) =>
    request<T>(path, {
      method: "POST",
      body,
    }),
  put: <T, B>(path: string, body: B) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
