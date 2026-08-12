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
