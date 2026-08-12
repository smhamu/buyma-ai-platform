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
    return <div className="panel">Loading diff...</div>;
  }

  if (error) {
    return (
      <div className="panel panel--error">
        <h3>Failed to load diff</h3>
        <p>{error}</p>
      </div>
    );
  }

  if (!diff) {
    return (
      <div className="panel panel--empty">
        <h3>Version Diff</h3>
        <p>Select a version to compare with the current document.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="page-section__header">
        <div>
          <h3>Version Diff</h3>
          <p>
            Current v{diff.base_version} vs Compare v{diff.compare_version}
          </p>
        </div>
        <div className="diff-stats">
          <span className="diff-pill diff-pill--added">Added {diff.added_count}</span>
          <span className="diff-pill diff-pill--removed">
            Removed {diff.removed_count}
          </span>
        </div>
      </div>

      {!diff.has_changes ? (
        <div className="panel panel--empty">
          <p>No changes between the selected versions.</p>
        </div>
      ) : (
        <div className="diff-view" role="region" aria-label="Document version diff">
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
