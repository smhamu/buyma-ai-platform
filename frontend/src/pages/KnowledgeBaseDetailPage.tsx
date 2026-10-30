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
                : "ナレッジベースの詳細を読み込めませんでした。",
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
    return <div className="page-status">ナレッジベースの詳細を読み込み中...</div>;
  }

  if (notFound) {
    return (
      <div className="panel panel--empty">
        <h1>ナレッジベースが見つかりません</h1><p>ナレッジベースが存在しないか、アクセス権限がありません。</p>
        <Link className="text-link" to="/knowledge-bases">
          ナレッジベース一覧へ戻る
        </Link>
      </div>
    );
  }

  if (error || !knowledgeBase || !stats) {
    return (
      <div className="panel panel--error">
        <h1>ナレッジベースの詳細を読み込めませんでした</h1><p>{error || "不明なエラー"}</p>
      </div>
    );
  }

  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <Link className="text-link" to="/knowledge-bases">
            ← ナレッジベース一覧
          </Link>
          <h1>{knowledgeBase.name}</h1>
          <p>{knowledgeBase.description || "説明はありません。"}</p>
        </div>
        <Badge tone={knowledgeBase.is_active ? "success" : "muted"}>
          {knowledgeBase.is_active ? "有効" : "無効"}
        </Badge>
      </div>

      <div className="status-grid">
        <StatusCard
          label="ドキュメント（全バージョン）"
          value={stats.document_count}
          helper="旧バージョンを含む"
        />
        <StatusCard
          label="最新ドキュメント"
          value={stats.latest_document_count}
          helper="最新バージョンのみ"
        />
        <StatusCard label="準備完了" value={stats.ready_count} /><StatusCard label="処理待ち" value={stats.pending_count} /><StatusCard label="処理中" value={stats.processing_count} /><StatusCard label="失敗" value={stats.failed_count} /><StatusCard label="チャンク" value={stats.chunk_count} /><StatusCard label="埋め込み" value={stats.embedding_count} />
      </div>

      <div className="panel">
        <h2>ドキュメント</h2>
        <p>
          ファイル、取込ジョブ、バージョン履歴を確認できます。
        </p>
        <Link
          className="secondary-button secondary-button--link"
          to={`/knowledge-bases/${knowledgeBase.id}/documents`}
        >
          ドキュメントを開く
        </Link>
      </div>
    </section>
  );
}
