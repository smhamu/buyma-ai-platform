import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  apiClient,
  configureApiClient,
} from "./api";

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
});
