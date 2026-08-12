export type KnowledgeBase = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
};

export type KnowledgeBaseStats = {
  document_count: number;
  latest_document_count: number;
  ready_count: number;
  pending_count: number;
  processing_count: number;
  failed_count: number;
  chunk_count: number;
  embedding_count: number;
};

export type DocumentItem = {
  id: string;
  knowledge_base_id: string | null;
  title: string;
  content: string;
  source_type: string;
  source_url: string | null;
  original_filename: string | null;
  mime_type: string | null;
  file_size: number | null;
  checksum: string | null;
  version: number;
  previous_document_id: string | null;
  version_group_id: string;
  is_latest: boolean;
  status: string;
  ingestion_status: "pending" | "processing" | "ready" | "failed" | string;
};

export type DocumentListQuery = {
  page: number;
  page_size: number;
  q?: string;
  ingestion_status?: string;
  source_type?: string;
  is_latest?: boolean;
  sort_by?: "created_at" | "updated_at" | "title" | "version" | "ingestion_status";
  sort_order?: "asc" | "desc";
};

export type DocumentListResponse = {
  items: DocumentItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  sort_by: string;
  sort_order: "asc" | "desc";
};

export type EmbeddingModel = {
  id: string;
  provider_id: string;
  model_name: string;
  model_version: string;
  dimension: number;
  distance_metric: string;
  is_active: boolean;
};

export type DocumentIngestionResponse = {
  filename: string;
  file_size: number;
  document: DocumentItem;
  chunks: Array<{
    id: string;
    document_id: string;
    chunk_index: number;
    content: string;
  }>;
  embedding_jobs: Array<{
    id: string;
    document_id: string;
    chunk_id: string;
    embedding_model_id: string;
    status: string;
    retry_count: number;
    error_message: string | null;
  }>;
  task_ids: string[];
};

export type RetryIngestionResponse = {
  document_id: string;
  retried_job_ids: string[];
  task_ids: string[];
  retried_count: number;
};
