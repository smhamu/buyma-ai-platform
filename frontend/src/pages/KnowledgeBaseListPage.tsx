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
              : "ナレッジベースを読み込めませんでした。",
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
    return <div className="page-status">ナレッジベースを読み込み中...</div>;
  }

  if (error) {
    return (
      <div className="panel panel--error">
        <h2>ナレッジベースを読み込めませんでした</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="panel panel--empty">
        <h2>ナレッジベースはまだありません</h2>
        <p>
          利用可能なナレッジベースが作成されると、ここに表示されます。
        </p>
      </div>
    );
  }

  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <h1>ナレッジベース</h1><p>利用可能なナレッジベースを確認できます。</p>
        </div>
      </div>

      <div className="kb-grid">
        {items.map((item) => (
          <article key={item.id} className="kb-card">
            <div className="kb-card__header">
              <h2 className="kb-card__title">{item.name}</h2>
              <Badge tone={item.is_active ? "success" : "muted"}>
                {item.is_active ? "有効" : "無効"}
              </Badge>
            </div>
            <p className="kb-card__description">
              {item.description || "説明はありません。"}
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
