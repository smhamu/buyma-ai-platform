import { FormEvent, useEffect, useState } from "react";

import { Badge } from "../ui/Badge";
import {
  deleteSupplierRakutenConfig,
  fetchSupplierRakutenConfig,
  saveSupplierRakutenConfig,
} from "../../modules/suppliers/api";
import type {
  Supplier,
  SupplierRakutenConfig,
  SupplierRakutenConfigInput,
} from "../../modules/suppliers/types";

const defaults: SupplierRakutenConfigInput = {
  advertiser_mid: 0,
  approval_status: "pending",
  sync_enabled: false,
  search_keyword: null,
  language: "en_US",
  max_results: 100,
  max_pages: 10,
  sync_interval_minutes: 1440,
};

const reasonLabels: Record<string, string> = {
  configuration_missing: "Rakuten連携設定が未登録です",
  advertiser_not_approved: "広告主の承認待ちです",
  sync_disabled: "同期が無効です",
  supplier_inactive: "仕入先が無効です",
  automated_fetch_disabled: "仕入先の自動取得が無効です",
  official_api_not_selected: "取込ソースが公式APIではありません",
  official_api_unavailable: "公式API利用可が未確認です",
  terms_not_allowed: "利用規約ステータスが許可ではありません",
  rakuten_token_missing: "Rakuten APIトークンが未設定です",
};

export function SupplierRakutenConfigPanel({ supplier, onClose }: { supplier: Supplier; onClose: () => void }) {
  const [setting, setSetting] = useState<SupplierRakutenConfig | null>(null);
  const [form, setForm] = useState(defaults);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void fetchSupplierRakutenConfig(supplier.id)
      .then((value) => {
        setSetting(value);
        if (value.configured) {
          setForm({
            advertiser_mid: value.advertiser_mid ?? 0,
            approval_status: value.approval_status,
            sync_enabled: value.sync_enabled,
            search_keyword: value.search_keyword,
            language: value.language,
            max_results: value.max_results,
            max_pages: value.max_pages,
            sync_interval_minutes: value.sync_interval_minutes,
          });
        }
      })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Rakuten連携設定を読み込めませんでした。"))
      .finally(() => setLoading(false));
  }, [supplier.id]);

  const field = <K extends keyof SupplierRakutenConfigInput>(key: K, value: SupplierRakutenConfigInput[K]) =>
    setForm((current) => ({ ...current, [key]: value }));

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true); setError(""); setNotice("");
    try {
      const saved = await saveSupplierRakutenConfig(supplier.id, form);
      setSetting(saved);
      setNotice("Rakuten連携設定を保存しました。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Rakuten連携設定を保存できませんでした。");
    } finally { setSaving(false); }
  };

  const remove = async () => {
    if (!window.confirm("この仕入先のRakuten連携設定を削除しますか？")) return;
    setSaving(true); setError(""); setNotice("");
    try {
      const removed = await deleteSupplierRakutenConfig(supplier.id);
      setSetting(removed); setForm(defaults);
      setNotice("Rakuten連携設定を削除しました。");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Rakuten連携設定を削除できませんでした。");
    } finally { setSaving(false); }
  };

  return <div className="modal-backdrop"><form className="modal-panel research-form" aria-label="Mytheresa Rakuten連携設定" onSubmit={(event) => void submit(event)}>
    <div className="modal-panel__header"><div><h2>Mytheresa Rakuten連携</h2><p>{supplier.name}</p></div><button type="button" className="secondary-button" onClick={onClose}>閉じる</button></div>
    {error && <div className="form-error-banner" role="alert">{error}</div>}
    {notice && <div className="panel" role="status">{notice}</div>}
    {loading ? <div className="page-status">設定を読み込み中...</div> : <>
      <div><Badge tone={setting?.can_sync ? "success" : "warning"}>{setting?.can_sync ? "同期可能" : "同期停止中"}</Badge></div>
      {setting && setting.blocked_reasons.length > 0 && <div className="form-help"><strong>同期を開始できない理由</strong><ul>{setting.blocked_reasons.map((reason) => <li key={reason}>{reasonLabels[reason] ?? reason}</li>)}</ul></div>}
      <label className="form-field">広告主MID<input className="form-field__input" type="number" min="1" required value={form.advertiser_mid || ""} onChange={(event) => field("advertiser_mid", Number(event.target.value))}/></label>
      <div className="form-grid">
        <label className="form-field">承認状態<select className="form-field__input" value={form.approval_status} onChange={(event) => { const value = event.target.value as SupplierRakutenConfigInput["approval_status"]; setForm((current) => ({ ...current, approval_status: value, sync_enabled: value === "approved" ? current.sync_enabled : false })); }}>
          <option value="not_applied">未申請</option><option value="pending">承認待ち</option><option value="approved">承認済み</option><option value="rejected">却下</option><option value="suspended">停止中</option>
        </select></label>
        <label className="form-field">言語<select className="form-field__input" value={form.language} onChange={(event) => field("language", event.target.value as SupplierRakutenConfigInput["language"])}><option>en_US</option><option>fr_FR</option><option>de_DE</option><option>pt_BR</option></select></label>
        <label className="form-field">1ページの商品数<input className="form-field__input" type="number" min="1" max="100" value={form.max_results} onChange={(event) => field("max_results", Number(event.target.value))}/></label>
        <label className="form-field">最大ページ数<input className="form-field__input" type="number" min="1" max="100" value={form.max_pages} onChange={(event) => field("max_pages", Number(event.target.value))}/></label>
        <label className="form-field">同期間隔（分）<input className="form-field__input" type="number" min="15" max="10080" value={form.sync_interval_minutes} onChange={(event) => field("sync_interval_minutes", Number(event.target.value))}/></label>
      </div>
      <label className="form-field">検索キーワード（任意）<input className="form-field__input" maxLength={200} value={form.search_keyword ?? ""} onChange={(event) => field("search_keyword", event.target.value || null)}/></label>
      <label className="checkbox-field"><input type="checkbox" checked={form.sync_enabled} disabled={form.approval_status !== "approved"} onChange={(event) => field("sync_enabled", event.target.checked)}/>商品同期を有効にする</label>
      <p className="form-help">承認待ちの間は同期を有効にできません。設定を保存しても、この画面からRakutenへの通信は発生しません。</p>
      <div className="row-actions"><button className="primary-button" disabled={saving}>{saving ? "保存中..." : "設定を保存"}</button>{setting?.configured && <button type="button" className="danger-button" disabled={saving} onClick={() => void remove()}>設定を削除</button>}</div>
    </>}
  </form></div>;
}
