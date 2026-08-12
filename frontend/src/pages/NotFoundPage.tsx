import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="panel panel--empty page-not-found">
      <h1>ページが見つかりません</h1>
      <Link className="text-link" to="/knowledge-bases">
        Knowledge Base一覧へ戻る
      </Link>
    </div>
  );
}
