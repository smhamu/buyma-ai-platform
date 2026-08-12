import { apiClient } from "../../lib/api";
import type {
  DocumentDetail,
  DocumentVersionDiffResponse,
  DocumentVersionListResponse,
  DocumentVersionRestoreResponse,
} from "./types";

export function getDocument(documentId: string) {
  return apiClient.get<DocumentDetail>(`/documents/${documentId}`);
}

export function getDocumentVersions(documentId: string) {
  return apiClient.get<DocumentVersionListResponse>(
    `/documents/${documentId}/versions`,
  );
}

export function getDocumentVersionDiff(
  documentId: string,
  compareDocumentId: string,
) {
  return apiClient.get<DocumentVersionDiffResponse>(
    `/documents/${documentId}/versions/${compareDocumentId}/diff`,
  );
}

export function restoreDocumentVersion(documentId: string) {
  return apiClient.post<DocumentVersionRestoreResponse, Record<string, never>>(
    `/documents/${documentId}/restore`,
    {},
  );
}
