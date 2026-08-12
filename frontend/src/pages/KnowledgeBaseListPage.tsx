import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "../components/ui/Badge";
import { ApiClientError } from "../lib/api";
import { fetchKnowledgeBases } from "../modules/knowledge-bases/api";
import type { KnowledgeBase } from "../modules/knowledge-bases/types";

export function KnowledgeBaseListPage() {
  const [items, setItems] = useState<KnowledgeBase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await fetchKnowledgeBases();
        if (!ignore) {
          setItems(result);
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof ApiClientError
              ? err.message
              : "Failed to load Knowledge Bases.",
          );
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
  }, []);

  if (isLoading) {
    return <div className="page-status">Loading Knowledge Bases...</div>;
  }

  if (error) {
    return (
      <div className="panel panel--error">
        <h2>Failed to load Knowledge Bases</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="panel panel--empty">
        <h2>No Knowledge Bases yet</h2>
        <p>
          No Knowledge Bases are available for this account. Once they are created
          on the backend, they will appear here.
        </p>
      </div>
    );
  }

  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <h1>Knowledge Bases</h1>
          <p>Review the Knowledge Bases available to your account.</p>
        </div>
      </div>

      <div className="kb-grid">
        {items.map((item) => (
          <article key={item.id} className="kb-card">
            <div className="kb-card__header">
              <h2 className="kb-card__title">{item.name}</h2>
              <Badge tone={item.is_active ? "success" : "muted"}>
                {item.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
            <p className="kb-card__description">
              {item.description || "No description provided."}
            </p>
            <Link className="text-link" to={`/knowledge-bases/${item.id}`}>
              View details
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
