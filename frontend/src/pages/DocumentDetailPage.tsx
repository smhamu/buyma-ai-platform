import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { RestoreConfirmDialog } from "../components/documents/RestoreConfirmDialog";
import { VersionDiffPanel } from "../components/documents/VersionDiffPanel";
import { Badge } from "../components/ui/Badge";
import { DocumentStatusBadge } from "../components/ui/DocumentStatusBadge";
import { ApiClientError } from "../lib/api";
import {
  getDocument,
  getDocumentVersionDiff,
  getDocumentVersions,
  restoreDocumentVersion,
} from "../modules/documents/api";
import type {
  DocumentDetail,
  DocumentVersion,
  DocumentVersionDiffResponse,
} from "../modules/documents/types";
import { fetchKnowledgeBase } from "../modules/knowledge-bases/api";
import type { KnowledgeBase } from "../modules/knowledge-bases/types";
import { label } from "../modules/product-research/format";

export function DocumentDetailPage() {
  const { knowledgeBaseId, documentId } = useParams<{
    knowledgeBaseId: string;
    documentId: string;
  }>();

  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [diff, setDiff] = useState<DocumentVersionDiffResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [versionsLoading, setVersionsLoading] = useState(true);
  const [diffLoading, setDiffLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [versionsError, setVersionsError] = useState<string | null>(null);
  const [diffError, setDiffError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [restoreTarget, setRestoreTarget] = useState<DocumentVersion | null>(null);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [selectedCompareId, setSelectedCompareId] = useState("");

  const latestVersion = useMemo(
    () => versions.find((item) => item.is_latest) ?? document,
    [versions, document],
  );

  useEffect(() => {
    if (!knowledgeBaseId || !documentId) {
      setNotFound(true);
      setLoading(false);
      return;
    }

    let ignore = false;

    const load = async () => {
      setLoading(true);
      setVersionsLoading(true);
      setError(null);
      setVersionsError(null);
      try {
        const [kb, currentDocument, versionList] = await Promise.all([
          fetchKnowledgeBase(knowledgeBaseId),
          getDocument(documentId),
          getDocumentVersions(documentId),
        ]);

        if (!ignore) {
          setKnowledgeBase(kb);
          setDocument(currentDocument);
          setVersions(versionList);
          setSelectedCompareId("");
          setNotFound(false);
        }
      } catch (err) {
        if (!ignore) {
          if (err instanceof ApiClientError && err.status === 404) {
            setNotFound(true);
          } else {
            setError(
              err instanceof ApiClientError
                ? err.message
                : "ドキュメント詳細を読み込めませんでした。",
            );
          }
        }
      } finally {
        if (!ignore) {
          setLoading(false);
          setVersionsLoading(false);
        }
      }
    };

    void load();
    return () => {
      ignore = true;
    };
  }, [knowledgeBaseId, documentId]);

  useEffect(() => {
    if (!documentId || !selectedCompareId) {
      setDiff(null);
      setDiffError(null);
      return;
    }

    let ignore = false;

    const loadDiff = async () => {
      setDiffLoading(true);
      setDiffError(null);
      try {
        const result = await getDocumentVersionDiff(documentId, selectedCompareId);
        if (!ignore) {
          setDiff(result);
        }
      } catch (err) {
        if (!ignore) {
          setDiff(null);
          setDiffError(
            err instanceof ApiClientError ? err.message : "差分を読み込めませんでした。",
          );
        }
      } finally {
        if (!ignore) {
          setDiffLoading(false);
        }
      }
    };

    void loadDiff();
    return () => {
      ignore = true;
    };
  }, [documentId, selectedCompareId]);

  const reloadVersions = async (focusDocumentId?: string) => {
    if (!documentId) return;

    setVersionsLoading(true);
    setVersionsError(null);
    try {
      const targetDocumentId = focusDocumentId ?? documentId;
      const [currentDocument, versionList] = await Promise.all([
        getDocument(targetDocumentId),
        getDocumentVersions(targetDocumentId),
      ]);
      setDocument(currentDocument);
      setVersions(versionList);
      setSelectedCompareId("");
      setDiff(null);
      setDiffError(null);
    } catch (err) {
      setVersionsError(
        err instanceof ApiClientError ? err.message : "バージョン履歴を更新できませんでした。",
      );
    } finally {
      setVersionsLoading(false);
    }
  };

  const handleRestore = async () => {
    if (!restoreTarget) return;

    setRestoring(true);
    setRestoreError(null);
    try {
      const result = await restoreDocumentVersion(restoreTarget.id);
      setRestoreTarget(null);
      await reloadVersions(result.new_document.id);
    } catch (err) {
      setRestoreError(
        err instanceof ApiClientError ? err.message : "バージョンを復元できませんでした。",
      );
    } finally {
      setRestoring(false);
    }
  };

  if (loading) {
    return <div className="page-status">ドキュメント詳細を読み込み中...</div>;
  }

  if (notFound) {
    return (
      <div className="panel panel--empty">
        <h1>ドキュメントが見つかりません</h1><p>ドキュメントが存在しないか、アクセス権限がありません。</p>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="panel panel--error">
        <h1>ドキュメント詳細を読み込めませんでした</h1>
        <p>{error || "不明なエラー"}</p>
      </div>
    );
  }

  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <Link
            className="text-link"
            to={`/knowledge-bases/${knowledgeBaseId}/documents`}
          >
            ← ドキュメント
          </Link>
          <h1>{document.title}</h1>
          <p>{knowledgeBase?.name ?? "ナレッジベース"}</p>
        </div>
      </div>

      <div className="detail-grid">
        <div className="panel">
          <h2>概要</h2>
          <div className="detail-list">
            <DetailRow label="タイトル" value={document.title} />
            <DetailRow label="ファイル名" value={document.original_filename ?? "-"} />
            <DetailRow label="ソース種別" value={label(document.source_type)} />
            <DetailRow label="バージョン" value={`v${document.version}`} />
            <DetailRow
              label="最新版"
              value={document.is_latest ? "最新" : "旧バージョン"}
            />
            <DetailRow label="ステータス" value={label(document.status)} />
            <DetailRow
              label="取込状態"
              value={<DocumentStatusBadge status={document.ingestion_status} />}
            />
            <DetailRow label="MIMEタイプ" value={document.mime_type ?? "-"} />
            <DetailRow
              label="ファイルサイズ"
              value={
                document.file_size !== null ? `${document.file_size}バイト` : "-"
              }
            />
            <DetailRow label="チェックサム" value={document.checksum ?? "-"} mono />
            <DetailRow label="ソースURL" value={document.source_url ?? "-"} mono />
          </div>
        </div>

        <div className="panel">
          <h2>バージョン履歴</h2>
          {versionsLoading ? (
            <p>バージョン履歴を読み込み中...</p>
          ) : versionsError ? (
            <div className="form-error-banner">{versionsError}</div>
          ) : versions.length === 0 ? (
            <p>バージョン履歴はありません。</p>
          ) : (
            <div className="version-list">
              {versions
                .slice()
                .sort((a, b) => b.version - a.version)
                .map((version) => (
                  <div key={version.id} className="version-item">
                    <div className="version-item__meta">
                      <div className="version-item__title">
                        v{version.version}
                        {version.is_latest ? <Badge tone="success">最新</Badge> : null}
                      </div>
                      <div className="version-item__sub">
                        <DocumentStatusBadge status={version.ingestion_status} />
                        <Badge tone="neutral">{label(version.source_type)}</Badge>
                      </div>
                      <div className="version-item__description">
                        <div>{version.title}</div>
                        <div>{version.original_filename ?? "-"}</div>
                      </div>
                    </div>
                    <div className="row-actions">
                      <button
                        className="secondary-button"
                        onClick={() => setSelectedCompareId(version.id)}
                        disabled={version.id === document.id}
                      >
                        差分
                      </button>
                      <button
                        className="secondary-button"
                        onClick={() => {
                          setRestoreError(null);
                          setRestoreTarget(version);
                        }}
                        disabled={version.is_latest}
                      >
                        復元
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>

      <VersionDiffPanel diff={diff} loading={diffLoading} error={diffError} />

      <RestoreConfirmDialog
        open={Boolean(restoreTarget)}
        version={restoreTarget?.version ?? null}
        latestVersion={latestVersion?.version ?? null}
        restoring={restoring}
        error={restoreError}
        onCancel={() => {
          if (!restoring) {
            setRestoreTarget(null);
            setRestoreError(null);
          }
        }}
        onConfirm={() => {
          void handleRestore();
        }}
      />
    </section>
  );
}

function DetailRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="detail-row">
      <div className="detail-row__label">{label}</div>
      <div className={`detail-row__value ${mono ? "detail-row__value--mono" : ""}`}>
        {value}
      </div>
    </div>
  );
}
