import { apiClient } from "../../lib/api";
import type { KnowledgeBase, KnowledgeBaseStats } from "./types";

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
