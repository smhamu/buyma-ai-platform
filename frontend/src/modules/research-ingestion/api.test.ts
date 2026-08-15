import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../../lib/api";
import { importResearchCsv } from "./api";

vi.mock("../../lib/api", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    postForm: vi.fn(),
    delete: vi.fn(),
  },
}));

describe("research ingestion API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("uploads CSV files as multipart form data", async () => {
    vi.mocked(apiClient.postForm).mockResolvedValue({
      success_count: 1,
      failed_count: 1,
      duplicate_count: 1,
      rows: [],
    });
    const file = new File(["supplier,brand"], "research.csv", {
      type: "text/csv",
    });

    await importResearchCsv(file);

    expect(apiClient.postForm).toHaveBeenCalledOnce();
    const [path, body] = vi.mocked(apiClient.postForm).mock.calls[0];
    expect(path).toBe("/research-ingestion/csv");
    expect(body).toBeInstanceOf(FormData);
    expect(body.get("file")).toBe(file);
    expect(apiClient.post).not.toHaveBeenCalled();
  });
});
