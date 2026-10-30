import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { DocumentUploadPanel } from "../components/documents/DocumentUploadPanel";
import { Badge } from "../components/ui/Badge";
import { DocumentStatusBadge } from "../components/ui/DocumentStatusBadge";
import { ApiClientError } from "../lib/api";
import {
  fetchKnowledgeBase,
  fetchKnowledgeBaseDocuments,
  retryDocumentIngestion,
} from "../modules/knowledge-bases/api";
import type {
  DocumentItem,
  DocumentListQuery,
  DocumentListResponse,
  KnowledgeBase,
} from "../modules/knowledge-bases/types";
import { label } from "../modules/product-research/format";

const POLLING_INTERVAL_MS = 3000;

function parseBooleanParam(value: string | null): boolean | undefined {
  if (value === "true") return true;
  if (value === "false") return false;
  return undefined;
}

export function KnowledgeBaseDocumentsPage() {
  const { knowledgeBaseId } = useParams<{ knowledgeBaseId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [response, setResponse] = useState<DocumentListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [searchInput, setSearchInput] = useState(searchParams.get("q") ?? "");
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);

  const query = useMemo<DocumentListQuery>(() => {
    return {
      page: Number(searchParams.get("page") ?? "1"),
      page_size: 20,
      q: searchParams.get("q") || undefined,
      ingestion_status:
        searchParams.get("ingestion_status") === "all"
          ? undefined
          : searchParams.get("ingestion_status") || undefined,
      source_type:
        searchParams.get("source_type") === "all"
          ? undefined
          : searchParams.get("source_type") || undefined,
      is_latest: parseBooleanParam(searchParams.get("is_latest") ?? "true"),
      sort_by:
        (searchParams.get("sort_by") as DocumentListQuery["sort_by"]) ??
        "created_at",
      sort_order:
        (searchParams.get("sort_order") as DocumentListQuery["sort_order"]) ??
        "desc",
    };
  }, [searchParams]);

  useEffect(() => {
    if (!knowledgeBaseId) {
      setNotFound(true);
      setLoading(false);
      return;
    }

    let ignore = false;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [kb, documents] = await Promise.all([
          fetchKnowledgeBase(knowledgeBaseId),
          fetchKnowledgeBaseDocuments(knowledgeBaseId, query),
        ]);
        if (!ignore) {
          setKnowledgeBase(kb);
          setResponse(documents);
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
                : "ドキュメントを読み込めませんでした。",
            );
          }
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    void load();
    return () => {
      ignore = true;
    };
  }, [knowledgeBaseId, query]);

  useEffect(() => {
    const shouldPoll = response?.items.some(
      (item) =>
        item.ingestion_status === "pending" ||
        item.ingestion_status === "processing",
    );

    if (!knowledgeBaseId || !shouldPoll) return;

    const timer = window.setInterval(async () => {
      try {
        const documents = await fetchKnowledgeBaseDocuments(knowledgeBaseId, query);
        setResponse(documents);
      } catch {
        window.clearInterval(timer);
      }
    }, POLLING_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
    };
  }, [knowledgeBaseId, query, response]);

  const updateQuery = (updates: Record<string, string | null>) => {
    const next = new URLSearchParams(searchParams);
    for (const [key, value] of Object.entries(updates)) {
      if (value === null || value === "") next.delete(key);
      else next.set(key, value);
    }
    setSearchParams(next);
  };

  const handleSearchSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateQuery({
      q: searchInput || null,
      page: "1",
    });
  };

  const handleRetry = async (documentId: string) => {
    setRetryingId(documentId);
    try {
      await retryDocumentIngestion(documentId);
      if (!knowledgeBaseId) return;
      const documents = await fetchKnowledgeBaseDocuments(knowledgeBaseId, query);
      setResponse(documents);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "再試行に失敗しました。");
    } finally {
      setRetryingId(null);
    }
  };

  const handleUploaded = async () => {
    if (!knowledgeBaseId) return;
    const documents = await fetchKnowledgeBaseDocuments(knowledgeBaseId, {
      ...query,
      page: 1,
    });
    setResponse(documents);
    updateQuery({ page: "1" });
  };

  if (loading) {
    return <div className="page-status">ドキュメントを読み込み中...</div>;
  }

  if (notFound) {
    return (
      <div className="panel panel--empty">
        <h1>ナレッジベースが見つかりません</h1><p>ナレッジベースが存在しないか、アクセス権限がありません。</p>
      </div>
    );
  }

  if (error && !response) {
    return (
      <div className="panel panel--error">
        <h1>ドキュメントを読み込めませんでした</h1>
        <p>{error}</p>
      </div>
    );
  }

  const items = response?.items ?? [];

  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <Link className="text-link" to={`/knowledge-bases/${knowledgeBaseId}`}>
            ← ナレッジベース詳細
          </Link>
          <h1>ドキュメント</h1>
          <p>{knowledgeBase?.name ?? "ナレッジベース"}</p>
        </div>
        <button className="primary-button" onClick={() => setUploadOpen(true)}>
          ドキュメントをアップロード
        </button>
      </div>

      <div className="panel">
        <form className="documents-toolbar" onSubmit={handleSearchSubmit}>
          <input
            className="form-field__input"
            placeholder="タイトルまたはファイル名を検索"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
          <select
            className="form-field__input"
            aria-label="取込ステータスで絞り込み"
            value={searchParams.get("ingestion_status") ?? "all"}
            onChange={(event) =>
              updateQuery({
                ingestion_status: event.target.value,
                page: "1",
              })
            }
          >
            <option value="all">すべてのステータス</option><option value="ready">準備完了</option><option value="pending">処理待ち</option><option value="processing">処理中</option><option value="failed">失敗</option>
          </select>
          <select
            className="form-field__input"
            aria-label="登録元で絞り込み"
            value={searchParams.get("source_type") ?? "all"}
            onChange={(event) =>
              updateQuery({
                source_type: event.target.value,
                page: "1",
              })
            }
          >
            <option value="all">すべての登録元</option><option value="file">ファイル</option><option value="manual">手動</option>
          </select>
          <select
            className="form-field__input"
            aria-label="バージョンで絞り込み"
            value={searchParams.get("is_latest") ?? "true"}
            onChange={(event) =>
              updateQuery({
                is_latest: event.target.value,
                page: "1",
              })
            }
          >
            <option value="true">最新のみ</option><option value="false">旧バージョン</option>
          </select>
          <select
            className="form-field__input"
            aria-label="ドキュメントの並び順"
            value={`${query.sort_by}:${query.sort_order}`}
            onChange={(event) => {
              const [sort_by, sort_order] = event.target.value.split(":");
              updateQuery({
                sort_by,
                sort_order,
              });
            }}
          >
            <option value="created_at:desc">作成日時（新しい順）</option><option value="created_at:asc">作成日時（古い順）</option><option value="updated_at:desc">更新日時（新しい順）</option><option value="updated_at:asc">更新日時（古い順）</option><option value="title:asc">タイトル（昇順）</option><option value="title:desc">タイトル（降順）</option><option value="version:desc">バージョン（降順）</option><option value="version:asc">バージョン（昇順）</option>
          </select>
          <button className="secondary-button" type="submit">
            検索
          </button>
        </form>
      </div>

      {error ? <div className="form-error-banner">{error}</div> : null}

      {items.length === 0 ? (
        <div className="panel panel--empty">
          <h2>ドキュメントがありません</h2>
          <p>
            {query.q || query.ingestion_status || query.source_type
              ? "検索または絞り込み条件に一致するドキュメントはありません。"
              : "このナレッジベースにはまだドキュメントがありません。"}
          </p>
        </div>
      ) : (
        <div className="panel">
          <div className="table-wrapper documents-table-desktop">
            <table className="data-table">
              <thead>
                <tr>
                  <th>タイトル</th><th>ファイル名</th><th>登録元</th><th>バージョン</th><th>取込状態</th><th>ステータス</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <DocumentRow
                    key={item.id}
                    item={item}
                    knowledgeBaseId={knowledgeBaseId}
                    retrying={retryingId === item.id}
                    onRetry={() => void handleRetry(item.id)}
                  />
                ))}
              </tbody>
            </table>
          </div>

          <div className="documents-card-list">
            {items.map((item) => (
              <article key={item.id} className="document-card">
                <div className="document-card__header">
                  <div className="table-primary">{item.title}</div>
                  <div className="document-card__badges">
                    <DocumentStatusBadge status={item.ingestion_status} />
                    <Badge tone="neutral">{label(item.source_type)}</Badge>
                  </div>
                </div>
                <div className="document-card__meta">
                  <div>ファイル名: {item.original_filename ?? "-"}</div>
                  <div>
                    バージョン: v{item.version}{" "}
                    {item.is_latest ? <Badge tone="success">最新</Badge> : null}
                  </div>
                  <div>ステータス: {label(item.status)}</div>
                </div>
                <div className="row-actions">
                  <Link
                    className="secondary-button secondary-button--link"
                    to={`/knowledge-bases/${knowledgeBaseId}/documents/${item.id}`}
                  >
                    詳細
                  </Link>
                  <button
                    className="secondary-button"
                    disabled={item.ingestion_status !== "failed" || retryingId === item.id}
                    onClick={() => void handleRetry(item.id)}
                  >
                    {retryingId === item.id ? "再試行中..." : "再試行"}
                  </button>
                </div>
              </article>
            ))}
          </div>

          <div className="pagination-bar">
            <div>
              ページ {response?.page} / {response?.total_pages} · 全{response?.total}件
            </div>
            <div className="pagination-actions">
              <button
                className="secondary-button"
                disabled={(response?.page ?? 1) <= 1}
                onClick={() =>
                  updateQuery({
                    page: String(Math.max(1, (response?.page ?? 1) - 1)),
                  })
                }
              >
                前へ
              </button>
              <button
                className="secondary-button"
                disabled={(response?.page ?? 1) >= (response?.total_pages ?? 1)}
                onClick={() =>
                  updateQuery({ page: String((response?.page ?? 1) + 1) })
                }
              >
                次へ
              </button>
            </div>
          </div>
        </div>
      )}

      <DocumentUploadPanel
        knowledgeBaseId={knowledgeBaseId ?? ""}
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onUploaded={() => {
          void handleUploaded();
        }}
      />
    </section>
  );
}

function DocumentRow({
  item,
  knowledgeBaseId,
  retrying,
  onRetry,
}: {
  item: DocumentItem;
  knowledgeBaseId?: string;
  retrying: boolean;
  onRetry: () => void;
}) {
  return (
    <tr>
      <td>
        <div className="table-primary">{item.title}</div>
      </td>
      <td>{item.original_filename ?? "-"}</td>
      <td>
        <Badge tone="neutral">{label(item.source_type)}</Badge>
      </td>
      <td>
        v{item.version} {item.is_latest ? <Badge tone="success">最新</Badge> : null}
      </td>
      <td>
        <DocumentStatusBadge status={item.ingestion_status} />
      </td>
      <td>{label(item.status)}</td>
      <td>
        <div className="row-actions">
          <Link
            className="secondary-button secondary-button--link"
            to={`/knowledge-bases/${knowledgeBaseId}/documents/${item.id}`}
          >
            詳細
          </Link>
          <button
            className="secondary-button"
            disabled={item.ingestion_status !== "failed" || retrying}
            onClick={onRetry}
          >
            {retrying ? "再試行中..." : "再試行"}
          </button>
        </div>
      </td>
    </tr>
  );
}
