import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { KnowledgeBaseDocumentsPage } from "./KnowledgeBaseDocumentsPage";

vi.mock("../modules/knowledge-bases/api", () => ({
  fetchKnowledgeBase: vi.fn(),
  fetchKnowledgeBaseDocuments: vi.fn(),
  fetchEmbeddingModels: vi.fn(),
  uploadKnowledgeBaseDocument: vi.fn(),
  retryDocumentIngestion: vi.fn(),
}));

import {
  fetchKnowledgeBase,
  fetchKnowledgeBaseDocuments,
  fetchEmbeddingModels,
  retryDocumentIngestion,
} from "../modules/knowledge-bases/api";

describe("KnowledgeBaseDocumentsPage", () => {
  it("renders document table", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(fetchKnowledgeBaseDocuments).mockResolvedValueOnce({
      items: [
        {
          id: "doc-1",
          knowledge_base_id: "kb-1",
          title: "Shipping Rule",
          content: "content",
          source_type: "file",
          source_url: null,
          original_filename: "shipping.pdf",
          mime_type: "application/pdf",
          file_size: 100,
          checksum: null,
          version: 1,
          previous_document_id: null,
          version_group_id: "vg-1",
          is_latest: true,
          status: "active",
          ingestion_status: "ready",
        },
      ],
      page: 1,
      page_size: 20,
      total: 1,
      total_pages: 1,
      sort_by: "created_at",
      sort_order: "desc",
    });

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents"
            element={<KnowledgeBaseDocumentsPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Shipping Rule")).toBeInTheDocument();
      expect(screen.getByText("shipping.pdf")).toBeInTheDocument();
    });
  });

  it("shows empty state when there are no documents", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(fetchKnowledgeBaseDocuments).mockResolvedValueOnce({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
      sort_by: "created_at",
      sort_order: "desc",
    });

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents"
            element={<KnowledgeBaseDocumentsPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("No documents found")).toBeInTheDocument();
    });
  });

  it("retries failed document ingestion", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValue({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(fetchKnowledgeBaseDocuments)
      .mockResolvedValueOnce({
        items: [
          {
            id: "doc-1",
            knowledge_base_id: "kb-1",
            title: "Failed Doc",
            content: "content",
            source_type: "file",
            source_url: null,
            original_filename: "failed.pdf",
            mime_type: "application/pdf",
            file_size: 100,
            checksum: null,
            version: 1,
            previous_document_id: null,
            version_group_id: "vg-1",
            is_latest: true,
            status: "active",
            ingestion_status: "failed",
          },
        ],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
        sort_by: "created_at",
        sort_order: "desc",
      })
      .mockResolvedValueOnce({
        items: [],
        page: 1,
        page_size: 20,
        total: 0,
        total_pages: 0,
        sort_by: "created_at",
        sort_order: "desc",
      });
    vi.mocked(retryDocumentIngestion).mockResolvedValueOnce({
      document_id: "doc-1",
      retried_job_ids: ["job-1"],
      task_ids: ["task-1"],
      retried_count: 1,
    });

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents"
            element={<KnowledgeBaseDocumentsPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Failed Doc")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    await waitFor(() => {
      expect(retryDocumentIngestion).toHaveBeenCalledWith("doc-1");
    });
  });

  it("opens upload panel", async () => {
    vi.mocked(fetchKnowledgeBase).mockResolvedValueOnce({
      id: "kb-1",
      name: "KB One",
      description: "desc",
      is_active: true,
    });
    vi.mocked(fetchKnowledgeBaseDocuments).mockResolvedValueOnce({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
      sort_by: "created_at",
      sort_order: "desc",
    });
    vi.mocked(fetchEmbeddingModels).mockResolvedValueOnce([
      {
        id: "model-1",
        provider_id: "provider-1",
        model_name: "text-embedding",
        model_version: "default",
        dimension: 1536,
        distance_metric: "cosine",
        is_active: true,
      },
    ]);

    render(
      <MemoryRouter initialEntries={["/knowledge-bases/kb-1/documents"]}>
        <Routes>
          <Route
            path="/knowledge-bases/:knowledgeBaseId/documents"
            element={<KnowledgeBaseDocumentsPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("No documents found")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Upload Document" }));

    await waitFor(() => {
      expect(screen.getByText("Upload a PDF, TXT, or Markdown file into this Knowledge Base.")).toBeInTheDocument();
    });
  });
});
