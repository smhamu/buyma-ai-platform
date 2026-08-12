import { apiClient } from "../../lib/api";
import type {
  DocumentIngestionResponse,
  DocumentListQuery,
  DocumentListResponse,
  EmbeddingModel,
  KnowledgeBase,
  KnowledgeBaseStats,
  RetryIngestionResponse,
} from "./types";

export function fetchKnowledgeBases() {
  return apiClient.get<KnowledgeBase[]>("/knowledge-bases");
}

export function fetchKnowledgeBase(knowledgeBaseId: string) {
  return apiClient.get<KnowledgeBase>(`/knowledge-bases/${knowledgeBaseId}`);
}

export function fetchKnowledgeBaseStats(knowledgeBaseId: string) {
  return apiClient.get<KnowledgeBaseStats>(
    `/knowledge-bases/${knowledgeBaseId}/stats`,
  );
}

export function fetchKnowledgeBaseDocuments(
  knowledgeBaseId: string,
  query: DocumentListQuery,
) {
  const search = new URLSearchParams();
  search.set("page", String(query.page));
  search.set("page_size", String(query.page_size));
  if (query.q) search.set("q", query.q);
  if (query.ingestion_status) search.set("ingestion_status", query.ingestion_status);
  if (query.source_type) search.set("source_type", query.source_type);
  if (typeof query.is_latest === "boolean") {
    search.set("is_latest", String(query.is_latest));
  }
  if (query.sort_by) search.set("sort_by", query.sort_by);
  if (query.sort_order) search.set("sort_order", query.sort_order);

  return apiClient.get<DocumentListResponse>(
    `/knowledge-bases/${knowledgeBaseId}/documents?${search.toString()}`,
  );
}

export function fetchEmbeddingModels() {
  return apiClient.get<EmbeddingModel[]>("/embedding-models");
}

export async function uploadKnowledgeBaseDocument(payload: {
  file: File;
  knowledgeBaseId: string;
  embeddingModelId: string;
  chunkSize: number;
  autoEnqueue: boolean;
}) {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("knowledge_base_id", payload.knowledgeBaseId);
  formData.append("embedding_model_id", payload.embeddingModelId);
  formData.append("chunk_size", String(payload.chunkSize));
  formData.append("auto_enqueue", String(payload.autoEnqueue));

  return apiClient.postForm<DocumentIngestionResponse>(
    "/documents/ingest-file",
    formData,
  );
}

export function retryDocumentIngestion(documentId: string) {
  return apiClient.post<RetryIngestionResponse, Record<string, never>>(
    `/documents/${documentId}/retry-ingestion`,
    {},
  );
}
