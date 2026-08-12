import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { Link, useSearchParams, useParams } from "react-router-dom";

import { DocumentStatusBadge } from "../components/ui/DocumentStatusBadge";
import { Badge } from "../components/ui/Badge";
import { DocumentUploadPanel } from "../components/documents/DocumentUploadPanel";
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
                : "Failed to load documents.",
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
      setError(
        err instanceof ApiClientError ? err.message : "Retry failed.",
      );
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
    return <div className="page-status">Loading documents...</div>;
  }

  if (notFound) {
    return (
      <div className="panel panel--empty">
        <h1>Knowledge Base not found</h1>
        <p>The Knowledge Base does not exist or you do not have access.</p>
      </div>
    );
  }

  if (error && !response) {
    return (
      <div className="panel panel--error">
        <h1>Failed to load documents</h1>
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
            ← Knowledge Base Detail
          </Link>
          <h1>Documents</h1>
          <p>{knowledgeBase?.name ?? "Knowledge Base"}</p>
        </div>
        <button className="primary-button" onClick={() => setUploadOpen(true)}>
          Upload Document
        </button>
      </div>

      <div className="panel">
        <form className="documents-toolbar" onSubmit={handleSearchSubmit}>
          <input
            className="form-field__input"
            placeholder="Search title or filename"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
          <select
            className="form-field__input"
            value={searchParams.get("ingestion_status") ?? "all"}
            onChange={(event) =>
              updateQuery({
                ingestion_status: event.target.value,
                page: "1",
              })
            }
          >
            <option value="all">All statuses</option>
            <option value="ready">Ready</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>
          <select
            className="form-field__input"
            value={searchParams.get("source_type") ?? "all"}
            onChange={(event) =>
              updateQuery({
                source_type: event.target.value,
                page: "1",
              })
            }
          >
            <option value="all">All sources</option>
            <option value="file">File</option>
            <option value="manual">Manual</option>
          </select>
          <select
            className="form-field__input"
            value={searchParams.get("is_latest") ?? "true"}
            onChange={(event) =>
              updateQuery({
                is_latest: event.target.value,
                page: "1",
              })
            }
          >
            <option value="true">Latest only</option>
            <option value="false">Old versions</option>
          </select>
          <select
            className="form-field__input"
            value={`${query.sort_by}:${query.sort_order}`}
            onChange={(event) => {
              const [sort_by, sort_order] = event.target.value.split(":");
              updateQuery({
                sort_by,
                sort_order,
              });
            }}
          >
            <option value="created_at:desc">Created desc</option>
            <option value="created_at:asc">Created asc</option>
            <option value="updated_at:desc">Updated desc</option>
            <option value="updated_at:asc">Updated asc</option>
            <option value="title:asc">Title asc</option>
            <option value="title:desc">Title desc</option>
            <option value="version:desc">Version desc</option>
            <option value="version:asc">Version asc</option>
          </select>
          <button className="secondary-button" type="submit">
            Search
          </button>
        </form>
      </div>

      {error ? <div className="form-error-banner">{error}</div> : null}

      {items.length === 0 ? (
        <div className="panel panel--empty">
          <h2>No documents found</h2>
          <p>
            {query.q || query.ingestion_status || query.source_type
              ? "No documents matched the current search or filters."
              : "There are no documents in this Knowledge Base yet."}
          </p>
        </div>
      ) : (
        <div className="panel">
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Filename</th>
                  <th>Source</th>
                  <th>Version</th>
                  <th>Ingestion</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <DocumentRow
                    key={item.id}
                    item={item}
                    retrying={retryingId === item.id}
                    onRetry={() => void handleRetry(item.id)}
                  />
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination-bar">
            <div>
              Page {response?.page} / {response?.total_pages} · Total {response?.total}
            </div>
            <div className="pagination-actions">
              <button
                className="secondary-button"
                disabled={(response?.page ?? 1) <= 1}
                onClick={() =>
                  updateQuery({ page: String(Math.max(1, (response?.page ?? 1) - 1)) })
                }
              >
                Previous
              </button>
              <button
                className="secondary-button"
                disabled={(response?.page ?? 1) >= (response?.total_pages ?? 1)}
                onClick={() =>
                  updateQuery({ page: String((response?.page ?? 1) + 1) })
                }
              >
                Next
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
  retrying,
  onRetry,
}: {
  item: DocumentItem;
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
        <Badge tone="neutral">{item.source_type}</Badge>
      </td>
      <td>
        v{item.version} {item.is_latest ? <Badge tone="success">Latest</Badge> : null}
      </td>
      <td>
        <DocumentStatusBadge status={item.ingestion_status} />
      </td>
      <td>{item.status}</td>
      <td>
        <div className="row-actions">
          <button className="secondary-button" disabled>
            Detail
          </button>
          <button className="secondary-button" disabled>
            Versions
          </button>
          <button
            className="secondary-button"
            disabled={item.ingestion_status !== "failed" || retrying}
            onClick={onRetry}
          >
            {retrying ? "Retrying..." : "Retry"}
          </button>
        </div>
      </td>
    </tr>
  );
}
