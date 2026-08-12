import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Badge } from "../components/ui/Badge";
import { StatusCard } from "../components/ui/StatusCard";
import { ApiClientError } from "../lib/api";
import {
  fetchKnowledgeBase,
  fetchKnowledgeBaseStats,
} from "../modules/knowledge-bases/api";
import type {
  KnowledgeBase,
  KnowledgeBaseStats,
} from "../modules/knowledge-bases/types";

export function KnowledgeBaseDetailPage() {
  const { knowledgeBaseId } = useParams<{ knowledgeBaseId: string }>();
  const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(null);
  const [stats, setStats] = useState<KnowledgeBaseStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!knowledgeBaseId) {
      setNotFound(true);
      setIsLoading(false);
      return;
    }

    let ignore = false;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      setNotFound(false);
      try {
        const [knowledgeBaseResult, statsResult] = await Promise.all([
          fetchKnowledgeBase(knowledgeBaseId),
          fetchKnowledgeBaseStats(knowledgeBaseId),
        ]);
        if (!ignore) {
          setKnowledgeBase(knowledgeBaseResult);
          setStats(statsResult);
        }
      } catch (err) {
        if (!ignore) {
          if (err instanceof ApiClientError && err.status === 404) {
            setNotFound(true);
          } else {
            setError(
              err instanceof ApiClientError
                ? err.message
                : "Failed to load Knowledge Base detail.",
            );
          }
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      ignore = true;
    };
  }, [knowledgeBaseId]);

  if (isLoading) {
    return <div className="page-status">Loading Knowledge Base detail...</div>;
  }

  if (notFound) {
    return (
      <div className="panel panel--empty">
        <h1>Knowledge Base not found</h1>
        <p>The Knowledge Base does not exist or you do not have access.</p>
        <Link className="text-link" to="/knowledge-bases">
          Back to Knowledge Bases
        </Link>
      </div>
    );
  }

  if (error || !knowledgeBase || !stats) {
    return (
      <div className="panel panel--error">
        <h1>Failed to load Knowledge Base detail</h1>
        <p>{error || "Unknown error"}</p>
      </div>
    );
  }

  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <Link className="text-link" to="/knowledge-bases">
            ← Knowledge Bases
          </Link>
          <h1>{knowledgeBase.name}</h1>
          <p>{knowledgeBase.description || "No description provided."}</p>
        </div>
        <Badge tone={knowledgeBase.is_active ? "success" : "muted"}>
          {knowledgeBase.is_active ? "Active" : "Inactive"}
        </Badge>
      </div>

      <div className="status-grid">
        <StatusCard
          label="Documents"
          value={stats.document_count}
          helper="All document versions"
        />
        <StatusCard
          label="Latest"
          value={stats.latest_document_count}
          helper="Latest versions only"
        />
        <StatusCard label="Ready" value={stats.ready_count} />
        <StatusCard label="Pending" value={stats.pending_count} />
        <StatusCard label="Processing" value={stats.processing_count} />
        <StatusCard label="Failed" value={stats.failed_count} />
        <StatusCard label="Chunks" value={stats.chunk_count} />
        <StatusCard label="Embeddings" value={stats.embedding_count} />
      </div>

      <div className="panel">
        <h2>Documents</h2>
        <p>
          Open the document list to review files, retry failed ingestion jobs, and
          inspect version history.
        </p>
        <Link
          className="secondary-button secondary-button--link"
          to={`/knowledge-bases/${knowledgeBase.id}/documents`}
        >
          Open Documents
        </Link>
      </div>
    </section>
  );
}
