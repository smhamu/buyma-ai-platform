import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { KnowledgeBaseDetailPage } from "./KnowledgeBaseDetailPage";

vi.mock("../modules/knowledge-bases/api", () => ({
  fetchKnowledgeBase: vi.fn(),
  fetchKnowledgeBaseStats: vi.fn(),
}));

import {
  fetchKnowledgeBase,
  fetchKnowledgeBaseStats,
} from "../modules/knowledge-bases/api";

describe("KnowledgeBaseDetailPage", () => {
  it("renders stats", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(fetchKnowledgeBaseStats).mockResolvedValueOnce({
      document_count: 10,
      latest_document_count: 8,
      ready_count: 6,
      pending_count: 1,
      processing_count: 1,
      failed_count: 0,
      chunk_count: 120,
      embedding_count: 120,
    });

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId"
            element={<KnowledgeBaseDetailPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("KB One")).toBeInTheDocument();
      expect(screen.getAllByText("120")).toHaveLength(2);
    });
  });
});
