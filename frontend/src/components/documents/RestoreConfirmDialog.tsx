export function RestoreConfirmDialog({
  open,
  version,
  latestVersion,
  restoring,
  error,
  onCancel,
  onConfirm,
}: {
  open: boolean;
  version: number | null;
  latestVersion: number | null;
  restoring: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  if (!open || version === null) return null;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-panel">
        <div className="modal-panel__header">
          <div>
            <h2>バージョン{version}を復元しますか？</h2>
            <p>
              旧バージョンの復元により、新しい最新バージョンが作成されます。既存の履歴は削除されません。
            </p>
            {latestVersion !== null ? <p>現在の最新バージョン: v{latestVersion}</p> : null}
          </div>
        </div>

        {error ? <div className="form-error-banner">{error}</div> : null}

        <div className="dialog-actions">
          <button className="secondary-button" onClick={onCancel} disabled={restoring}>
            キャンセル
          </button>
          <button className="primary-button" onClick={onConfirm} disabled={restoring}>
            {restoring ? "復元中..." : "復元"}
          </button>
        </div>
      </div>
    </div>
  );
}
