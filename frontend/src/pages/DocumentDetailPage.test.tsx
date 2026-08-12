import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { ApiClientError } from "../lib/api";
import { DocumentDetailPage } from "./DocumentDetailPage";

vi.mock("../modules/knowledge-bases/api", () => ({
  fetchKnowledgeBase: vi.fn(),
}));

vi.mock("../modules/documents/api", () => ({
  getDocument: vi.fn(),
  getDocumentVersions: vi.fn(),
  getDocumentVersionDiff: vi.fn(),
  restoreDocumentVersion: vi.fn(),
}));

import { fetchKnowledgeBase } from "../modules/knowledge-bases/api";
import {
  getDocument,
  getDocumentVersionDiff,
  getDocumentVersions,
  restoreDocumentVersion,
} from "../modules/documents/api";

const baseDocument = {
  id: "doc-2",
  knowledge_base_id: "kb-1",
  title: "Current Rule",
  content: "line 1\nline 2",
  source_type: "file",
  source_url: null,
  original_filename: "rule-v2.txt",
  mime_type: "text/plain",
  file_size: 20,
  checksum: "abc",
  version: 2,
  previous_document_id: "doc-1",
  version_group_id: "vg-1",
  is_latest: true,
  status: "active",
  ingestion_status: "ready",
};

const oldVersion = {
  ...baseDocument,
  id: "doc-1",
  title: "Old Rule",
  original_filename: "rule-v1.txt",
  version: 1,
  previous_document_id: null,
  is_latest: false,
};

describe("DocumentDetailPage", () => {
  it("renders document detail and version history", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(getDocument).mockResolvedValueOnce(baseDocument);
    vi.mocked(getDocumentVersions).mockResolvedValueOnce([oldVersion, baseDocument]);

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents/doc-2"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents/:documentId"
            element={<DocumentDetailPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Current Rule" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("heading", { name: "Version History" }),
      ).toBeInTheDocument();
      expect(screen.getAllByText("rule-v2.txt").length).toBeGreaterThan(0);
      expect(screen.getAllByText("rule-v1.txt").length).toBeGreaterThan(0);
    });
  });

  it("shows document not found state", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(getDocument).mockRejectedValueOnce(
      new ApiClientError(404, "DOCUMENT_NOT_FOUND", "Document not found."),
    );
    vi.mocked(getDocumentVersions).mockResolvedValueOnce([]);

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents/doc-x"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents/:documentId"
            element={<DocumentDetailPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Document not found")).toBeInTheDocument();
    });
  });

  it("loads diff for selected version", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(getDocument).mockResolvedValueOnce(baseDocument);
    vi.mocked(getDocumentVersions).mockResolvedValueOnce([oldVersion, baseDocument]);
    vi.mocked(getDocumentVersionDiff).mockResolvedValueOnce({
      base_document_id: "doc-2",
      base_version: 2,
      compare_document_id: "doc-1",
      compare_version: 1,
      lines: [
        { type: "removed", content: "old" },
        { type: "added", content: "new" },
      ],
      added_count: 1,
      removed_count: 1,
      unchanged_count: 0,
      has_changes: true,
    });

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents/doc-2"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents/:documentId"
            element={<DocumentDetailPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Current Rule" }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "Diff" })[1]);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Version Diff" }),
      ).toBeInTheDocument();
      expect(screen.getByText(/Added\s*1/)).toBeInTheDocument();
      expect(screen.getByText(/Removed\s*1/)).toBeInTheDocument();
    });
  });

  it("shows no changes diff state", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(getDocument).mockResolvedValueOnce(baseDocument);
    vi.mocked(getDocumentVersions).mockResolvedValueOnce([oldVersion, baseDocument]);
    vi.mocked(getDocumentVersionDiff).mockResolvedValueOnce({
      base_document_id: "doc-2",
      base_version: 2,
      compare_document_id: "doc-1",
      compare_version: 1,
      lines: [],
      added_count: 0,
      removed_count: 0,
      unchanged_count: 0,
      has_changes: false,
    });

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents/doc-2"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents/:documentId"
            element={<DocumentDetailPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Current Rule" }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "Diff" })[1]);

    await waitFor(() => {
      expect(
        screen.getByText("No changes between the selected versions."),
      ).toBeInTheDocument();
    });
  });

  it("restores an old version", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(getDocument)
      .mockResolvedValueOnce(baseDocument)
      .mockResolvedValueOnce({
        ...baseDocument,
        id: "doc-3",
        version: 3,
      });
    vi.mocked(getDocumentVersions)
      .mockResolvedValueOnce([oldVersion, baseDocument])
      .mockResolvedValueOnce([
        oldVersion,
        baseDocument,
        {
          ...baseDocument,
          id: "doc-3",
          version: 3,
          is_latest: true,
        },
      ]);
    vi.mocked(restoreDocumentVersion).mockResolvedValueOnce({
      restored_from_document_id: "doc-1",
      restored_from_version: 1,
      new_document: {
        ...baseDocument,
        id: "doc-3",
        version: 3,
        is_latest: true,
      },
      task_ids: [],
    });

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents/doc-2"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents/:documentId"
            element={<DocumentDetailPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "Current Rule" }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: "Restore" })[1]);

    await waitFor(() => {
      expect(screen.getByText("Restore version 1?")).toBeInTheDocument();
    });

    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Restore" }));

    await waitFor(() => {
      expect(restoreDocumentVersion).toHaveBeenCalledWith("doc-1");
    });
  });
});
