import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiClientError } from "../lib/api";
import { fetchKnowledgeBases } from "../modules/knowledge-bases/api";
import type { KnowledgeBase } from "../modules/knowledge-bases/types";
import { Badge } from "../components/ui/Badge";

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
              : "Knowledge Base一覧の取得に失敗しました。",
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
    return <div className="page-status">Knowledge Base一覧を読み込み中...</div>;
  }

  if (error) {
    return (
      <div className="panel panel--error">
        <h2>読み込みに失敗しました</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="panel panel--empty">
        <h2>Knowledge Base がまだありません</h2>
        <p>
          作成済みのKnowledge Baseが0件です。backend側で作成後、この一覧に表示されます。
        </p>
      </div>
    );
  }

  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <h1>Knowledge Bases</h1>
          <p>利用可能なKnowledge Baseを確認できます。</p>
        </div>
      </div>

      <div className="kb-grid">
        {items.map((item) => (
          <article key={item.id} className="kb-card">
            <div className="kb-card__header">
              <h2>{item.name}</h2>
              <Badge tone={item.is_active ? "success" : "muted"}>
                {item.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
            <p className="kb-card__description">
              {item.description || "説明は未設定です。"}
            </p>
            <Link className="text-link" to={`/knowledge-bases/${item.id}`}>
              詳細を見る
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
