import { Link } from "react-router-dom";

export function NotFoundPage() {
  return <div className="panel panel--empty page-not-found"><h1>ページが見つかりません</h1><p>指定されたページは存在しないか、アクセスできません。</p><Link className="text-link" to="/knowledge-bases">ナレッジベース一覧へ戻る</Link></div>;
}
