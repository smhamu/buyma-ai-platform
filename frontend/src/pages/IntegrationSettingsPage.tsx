import { FormEvent, useEffect, useState } from "react";

import { Badge } from "../components/ui/Badge";
import {
  fetchRakutenSetting,
  removeRakutenToken,
  saveRakutenToken,
} from "../modules/integration-settings/api";
import type { RakutenTokenSetting } from "../modules/integration-settings/types";

const empty: RakutenTokenSetting = {
  provider: "rakuten_product_search",
  configured: false,
};

export function IntegrationSettingsPage() {
  const [setting, setSetting] = useState(empty);
  const [token, setToken] = useState("");
  const [changing, setChanging] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void fetchRakutenSetting()
      .then(setSetting)
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "連携設定を読み込めませんでした。"),
      )
      .finally(() => setLoading(false));
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      setSetting(await saveRakutenToken({ token }));
      setToken("");
      setChanging(false);
      setNotice("Rakuten APIトークンを保存しました。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Rakuten APIトークンを保存できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!window.confirm("Rakuten APIトークンを削除しますか？")) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      setSetting(await removeRakutenToken());
      setToken("");
      setChanging(false);
      setNotice("Rakuten APIトークンを削除しました。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Rakuten APIトークンを削除できませんでした。");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="page-status">連携設定を読み込み中...</div>;

  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <h1>外部サービス連携</h1>
          <p>商品リサーチに使用する外部APIの認証情報を管理します。</p>
        </div>
      </div>
      {error && <div className="form-error-banner" role="alert">{error}</div>}
      {notice && <div className="panel" role="status">{notice}</div>}
      <form className="panel notification-settings" aria-label="Rakuten API設定" onSubmit={(event) => void submit(event)}>
        <div className="notification-settings__header">
          <div>
            <h2>Rakuten Advertising Product Search</h2>
            <Badge tone={setting.configured ? "success" : "warning"}>
              {setting.configured ? "設定済み" : "未設定"}
            </Badge>
          </div>
        </div>
        {(!setting.configured || changing) && (
          <label className="form-field">
            APIトークン
            <input
              className="form-field__input"
              type="password"
              required
              maxLength={4096}
              value={token}
              onChange={(event) => setToken(event.target.value)}
              autoComplete="new-password"
            />
          </label>
        )}
        {setting.configured && !changing && <p><strong>APIトークン:</strong> 設定済み</p>}
        <p className="form-help">
          トークンは安全なシークレットストアに保存され、保存後に画面やAPIへ再表示されません。
        </p>
        <div className="row-actions">
          {(!setting.configured || changing) && (
            <button className="primary-button" disabled={saving || !token}>
              {saving ? "保存中..." : "トークンを保存"}
            </button>
          )}
          {setting.configured && (
            <button type="button" className="secondary-button" onClick={() => { setChanging((value) => !value); setToken(""); }}>
              {changing ? "変更をキャンセル" : "トークンを変更"}
            </button>
          )}
          {setting.configured && (
            <button type="button" className="danger-button" onClick={() => void remove()} disabled={saving}>
              トークンを削除
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
