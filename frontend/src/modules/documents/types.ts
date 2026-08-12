import type { DocumentItem } from "../knowledge-bases/types";

export type DocumentDetail = DocumentItem;

export type DocumentVersion = DocumentItem;

export type DocumentVersionListResponse = DocumentVersion[];

export type DocumentVersionDiffLine = {
  type: "added" | "removed" | "unchanged" | string;
  content: string;
};

export type DocumentVersionDiffResponse = {
  base_document_id: string;
  base_version: number;
  compare_document_id: string;
  compare_version: number;
  lines: DocumentVersionDiffLine[];
  added_count: number;
  removed_count: number;
  unchanged_count: number;
  has_changes: boolean;
};

export type DocumentVersionRestoreResponse = {
  restored_from_document_id: string;
  restored_from_version: number;
  new_document: DocumentItem;
  task_ids: string[];
};
