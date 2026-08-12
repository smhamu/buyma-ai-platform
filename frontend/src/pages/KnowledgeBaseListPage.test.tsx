import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { KnowledgeBaseListPage } from "./KnowledgeBaseListPage";

vi.mock("../modules/knowledge-bases/api", () => ({
  fetchKnowledgeBases: vi.fn(),
}));

import { fetchKnowledgeBases } from "../modules/knowledge-bases/api";

describe("KnowledgeBaseListPage", () => {
  it("shows empty state", async () => {
    vi.mocked(fetchKnowledgeBases).mockResolvedValueOnce([]);

    render(
      <MemoryRouter>
        <KnowledgeBaseListPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Knowledge Base がまだありません"),
      ).toBeInTheDocument();
    });
  });

  it("shows list items", async () => {
    vi.mocked(fetchKnowledgeBases).mockResolvedValueOnce([
      {
        id: "kb-1",
        name: "KB One",
        description: "desc",
        is_active: true,
      },
    ]);

    render(
      <MemoryRouter>
        <KnowledgeBaseListPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("KB One")).toBeInTheDocument();
    });
  });
});
