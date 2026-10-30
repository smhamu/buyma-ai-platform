import { FormEvent, useEffect, useMemo, useState } from "react";

import { ApiClientError } from "../../lib/api";
import {
  fetchEmbeddingModels,
  uploadKnowledgeBaseDocument,
} from "../../modules/knowledge-bases/api";
import type { DocumentIngestionResponse, EmbeddingModel } from "../../modules/knowledge-bases/types";

const ACCEPTED_FILE_TYPES = ".pdf,.txt,.md,.markdown";
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

export function DocumentUploadPanel({
  knowledgeBaseId,
  open,
  onClose,
  onUploaded,
}: {
  knowledgeBaseId: string;
  open: boolean;
  onClose: () => void;
  onUploaded: (response: DocumentIngestionResponse) => void;
}) {
  const [models, setModels] = useState<EmbeddingModel[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [embeddingModelId, setEmbeddingModelId] = useState("");
  const [chunkSize, setChunkSize] = useState("500");
  const [autoEnqueue, setAutoEnqueue] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    let ignore = false;
    const loadModels = async () => {
      setLoadingModels(true);
      try {
        const result = await fetchEmbeddingModels();
        if (!ignore) {
          const activeModels = result.filter((model) => model.is_active);
          setModels(activeModels);
          setEmbeddingModelId(activeModels[0]?.id ?? "");
        }
      } catch (err) {
        if (!ignore) {
          setError(
            err instanceof ApiClientError
              ? err.message
              : "埋め込みモデルを読み込めませんでした。",
          );
        }
      } finally {
        if (!ignore) setLoadingModels(false);
      }
    };
    void loadModels();
    return () => {
      ignore = true;
    };
  }, [open]);

  const selectedModelLabel = useMemo(() => {
    const model = models.find((item) => item.id === embeddingModelId);
    return model ? `${model.model_name} (${model.model_version})` : "";
  }, [models, embeddingModelId]);

  if (!open) return null;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!file) {
      setError("ファイルを選択してください。");
      return;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError("ファイルサイズは10MB以下にしてください。");
      return;
    }
    if (!embeddingModelId) {
      setError("埋め込みモデルを選択してください。");
      return;
    }

    setSubmitting(true);
    try {
      const result = await uploadKnowledgeBaseDocument({
        file,
        knowledgeBaseId,
        embeddingModelId,
        chunkSize: Number(chunkSize),
        autoEnqueue,
      });
      onUploaded(result);
      onClose();
      setFile(null);
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "アップロードに失敗しました。",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-panel">
        <div className="modal-panel__header">
          <div>
            <h2>ドキュメントをアップロード</h2><p>PDF、TXT、Markdownファイルをこのナレッジベースへ追加します。</p>
          </div>
          <button className="secondary-button" onClick={onClose} type="button">
            閉じる
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span className="form-field__label">ファイル</span>
            <input
              className="form-field__input"
              type="file"
              accept={ACCEPTED_FILE_TYPES}
              onChange={(event) => {
                const nextFile = event.target.files?.[0] ?? null;
                setFile(nextFile);
              }}
            />
          </label>

          <label className="form-field">
            <span className="form-field__label">埋め込みモデル</span>
            <select
              className="form-field__input"
              value={embeddingModelId}
              onChange={(event) => setEmbeddingModelId(event.target.value)}
              disabled={loadingModels}
            >
              <option value="">モデルを選択</option>
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.model_name} ({model.model_version})
                </option>
              ))}
            </select>
            {selectedModelLabel ? (
              <span className="form-field__hint">{selectedModelLabel}</span>
            ) : null}
          </label>

          <label className="form-field">
            <span className="form-field__label">チャンクサイズ</span>
            <input
              className="form-field__input"
              type="number"
              min={100}
              max={5000}
              value={chunkSize}
              onChange={(event) => setChunkSize(event.target.value)}
            />
          </label>

          <label className="checkbox-field">
            <input
              type="checkbox"
              checked={autoEnqueue}
              onChange={(event) => setAutoEnqueue(event.target.checked)}
            />
            <span>埋め込みジョブを自動登録</span>
          </label>

          {error ? <div className="form-error-banner">{error}</div> : null}

          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? "アップロード中..." : "アップロード"}
          </button>
        </form>
      </div>
    </div>
  );
}
