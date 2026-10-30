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

const ERROR_MESSAGES:Record<string,string>={CATEGORY_PURCHASE_RESTRICTED:"このカテゴリは購入制限の対象です。",PRODUCT_PURCHASE_RESTRICTED:"この商品は購入制限の対象です。",SUPPLIER_PROHIBITED:"この仕入先はBUYMAの買付先として利用できません。",SUPPLIER_DOES_NOT_SHIP_TO_JAPAN:"この仕入先は日本へ配送していません。",ONLINE_PURCHASE_UNAVAILABLE:"オンラインで購入できない商品です。",PRODUCT_OUT_OF_STOCK:"商品は在庫切れです。",SOURCE_IN_USE:"候補へ変換済みの取込ソースは削除できません。",SOURCE_ALREADY_CONVERTED:"この取込ソースには既に候補が作成されています。"};

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
      ERROR_MESSAGES[error.code] || error.message || "リクエストに失敗しました。",
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
