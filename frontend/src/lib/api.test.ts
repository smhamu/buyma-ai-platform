import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, apiClient, configureApiClient } from "./api";

describe("apiClient", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
    configureApiClient({
      getAccessToken: () => "token",
      refreshAccessToken: async () => null,
      onUnauthorized: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns response data for successful requests", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          message: "ok",
          data: [{ id: "1", name: "kb", description: null, is_active: true }],
        }),
        { status: 200 },
      ),
    );

    const data = await apiClient.get<Array<{ id: string }>>("/knowledge-bases");

    expect(data).toHaveLength(1);
  });

  it("throws standardized api errors", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(
        JSON.stringify({
          success: false,
          code: "INVALID_CREDENTIALS",
          message: "Invalid email or password.",
        }),
        { status: 401 },
      ),
    );

    await expect(apiClient.get("/auth/me")).rejects.toBeInstanceOf(
      ApiClientError,
    );
  });

  it("lets the browser set multipart content type and boundary", async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          message: "uploaded",
          data: { success_count: 1 },
        }),
        { status: 200 },
      ),
    );
    const body = new FormData();
    const file = new File(["supplier,brand"], "research.csv", {
      type: "text/csv",
    });
    body.append("file", file);

    await apiClient.postForm("/research-ingestion/csv", body);

    const [, init] = vi.mocked(fetch).mock.calls[0];
    expect(init?.body).toBe(body);
    const headers = new Headers(init?.headers);
    expect(headers.has("Content-Type")).toBe(false);
    expect(headers.get("Authorization")).toBe("Bearer token");
    expect(body.get("file")).toBe(file);
  });
});
