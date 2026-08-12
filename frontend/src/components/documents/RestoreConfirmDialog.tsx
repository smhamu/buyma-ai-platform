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
            <h2>Restore version {version}?</h2>
            <p>
              Restoring an old version will create a new latest version.
              Existing version history will not be deleted.
            </p>
            {latestVersion !== null ? <p>Current latest version: v{latestVersion}</p> : null}
          </div>
        </div>

        {error ? <div className="form-error-banner">{error}</div> : null}

        <div className="dialog-actions">
          <button className="secondary-button" onClick={onCancel} disabled={restoring}>
            Cancel
          </button>
          <button className="primary-button" onClick={onConfirm} disabled={restoring}>
            {restoring ? "Restoring..." : "Restore"}
          </button>
        </div>
      </div>
    </div>
  );
}
