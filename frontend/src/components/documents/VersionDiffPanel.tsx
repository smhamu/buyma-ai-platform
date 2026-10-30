import type { DocumentVersionDiffResponse } from "../../modules/documents/types";

export function VersionDiffPanel({
  diff,
  loading,
  error,
}: {
  diff: DocumentVersionDiffResponse | null;
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return <div className="panel">差分を読み込み中...</div>;
  }

  if (error) {
    return (
      <div className="panel panel--error">
        <h3>差分を読み込めませんでした</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!diff) {
    return (
      <div className="panel panel--empty">
        <h3>バージョン差分</h3><p>現在のドキュメントと比較するバージョンを選択してください。</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="page-section__header">
        <div>
          <h3>バージョン差分</h3>
          <p>
            現在 v{diff.base_version} ／ 比較対象 v{diff.compare_version}
          </p>
        </div>
        <div className="diff-stats">
          <span className="diff-pill diff-pill--added">追加 {diff.added_count}</span>
          <span className="diff-pill diff-pill--removed">
            削除 {diff.removed_count}
          </span>
        </div>
      </div>

      {!diff.has_changes ? (
        <div className="panel panel--empty">
          <p>選択したバージョン間に変更はありません。</p>
        </div>
      ) : (
        <div className="diff-view" role="region" aria-label="ドキュメントのバージョン差分">
          <pre className="diff-code">
            {diff.lines.map((line, index) => {
              const prefix =
                line.type === "added"
                  ? "+"
                  : line.type === "removed"
                    ? "-"
                    : " ";
              return (
                <div
                  key={`${index}-${line.type}`}
                  className={`diff-line diff-line--${line.type}`}
                >
                  <span className="diff-line__prefix">{prefix}</span>
                  <span>{line.content}</span>
                </div>
              );
            })}
          </pre>
        </div>
      )}
    </div>
  );
}
