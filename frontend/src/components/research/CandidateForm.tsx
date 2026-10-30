import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ApiClientError } from "../../lib/api";
import { fetchBrands } from "../../modules/brands/api";
import type { Brand } from "../../modules/brands/types";
import {
  fetchProductCategories,
  resolvePurchasePolicy,
} from "../../modules/product-categories/api";
import type {
  ProductCategory,
  ResolvedPolicy,
} from "../../modules/product-categories/types";
import {
  calculateCandidate,
  createCandidate,
  updateCandidate,
} from "../../modules/product-research/api";
import {
  money,
  percent,
  label as displayLabel,
} from "../../modules/product-research/format";
import type {
  Candidate,
  CandidateInput,
  PricePreview,
} from "../../modules/product-research/types";
import { fetchSuppliers } from "../../modules/suppliers/api";
import type { Supplier } from "../../modules/suppliers/types";

const blank: CandidateInput = {
  supplier_id: "",
  brand_id: "",
  category_id: null,
  supplier_product_url: "",
  supplier_product_code: null,
  product_name: "",
  category: null,
  supplier_price: "",
  supplier_currency: "EUR",
  vat_policy: "unknown",
  vat_rate: null,
  japan_shipping_cost: "0",
  exchange_rate: "",
  estimated_import_cost: "0",
  estimated_other_cost: "0",
  buyma_price: "",
  buyma_fee_rate: "0.077",
  availability_status: "unknown",
  purchase_restriction: "unknown",
  research_status: "discovered",
  checked_at: null,
  online_purchase_available: true,
  is_active: true,
};
const messages: Record<string, string> = {
  BRAND_RESEARCH_DISABLED: "このブランドは調査対象外です。",
  BRAND_RESEARCH_ONLY: "このブランドは調査のみ許可されています。",
  CATEGORY_PURCHASE_RESTRICTED:
    "このカテゴリの購入ポリシーでは出品準備完了にできません。",
  SUPPLIER_PROHIBITED: "この仕入先はBUYMAでの買付が禁止されています。",
  SUPPLIER_DOES_NOT_SHIP_TO_JAPAN: "この仕入先は日本へ配送できません。",
  ONLINE_PURCHASE_UNAVAILABLE: "この商品は現在オンラインで購入できません。",
  PRODUCT_OUT_OF_STOCK: "在庫切れの商品は出品準備完了にできません。",
};

export function CandidateForm({
  candidate,
  onClose,
  onSaved,
}: {
  candidate?: Candidate;
  onClose: () => void;
  onSaved?: () => void;
}) {
  const navigate = useNavigate();
  const [form, setForm] = useState<CandidateInput>(
    candidate ? { ...candidate } : blank,
  );
  const [brands, setBrands] = useState<Brand[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [resolved, setResolved] = useState<ResolvedPolicy | null>(null);
  const [preview, setPreview] = useState<PricePreview | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    void Promise.all([
      fetchBrands({ page_size: 100, is_active: undefined }),
      fetchSuppliers({ page_size: 100, is_active: undefined }),
      fetchProductCategories(),
    ])
      .then(([b, s, c]) => {
        setBrands(b.items);
        setSuppliers(s.items);
        setCategories(c);
      })
      .catch(() => setError("マスターデータを読み込めませんでした。"));
  }, []);
  useEffect(() => {
    if (!form.brand_id) {
      setResolved(null);
      return;
    }
    void resolvePurchasePolicy(form.brand_id, form.category_id || null)
      .then(setResolved)
      .catch(() => setResolved(null));
  }, [form.brand_id, form.category_id]);
  const field = (key: keyof CandidateInput, value: unknown) => {
    setForm({ ...form, [key]: value });
    setPreview(null);
  };
  const valid = () =>
    form.brand_id &&
    form.supplier_id &&
    form.product_name &&
    form.supplier_product_url &&
    form.supplier_price &&
    form.exchange_rate &&
    form.buyma_price;
  const fail = (x: unknown) =>
    setError(
      x instanceof ApiClientError
        ? messages[x.code] || x.message
        : "リクエストに失敗しました。",
    );
  const calculate = async () => {
    if (!valid()) {
      setError("利益計算の前に必須項目をすべて入力してください。");
      return;
    }
    setBusy(true);
    try {
      setPreview(await calculateCandidate(form));
      setError("");
    } catch (x) {
      fail(x);
    } finally {
      setBusy(false);
    }
  };
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!valid()) {
      setError("必須項目をすべて入力してください。");
      return;
    }
    setBusy(true);
    try {
      const saved = candidate
        ? await updateCandidate(candidate.id, form)
        : await createCandidate(form);
      onSaved?.();
      onClose();
      navigate(`/product-research/${saved.id}`);
    } catch (x) {
      fail(x);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="modal-backdrop">
      <form
        className="modal-panel candidate-form"
        aria-label="商品リサーチ候補フォーム"
        onSubmit={(e) => void submit(e)}
      >
        <div className="modal-panel__header">
          <div>
            <h2>
              {candidate ? "商品リサーチ候補を編集" : "商品リサーチ候補を追加"}
            </h2>
          <p>利益はサーバー側で計算されます。</p>
          </div>
          <button type="button" className="secondary-button" onClick={onClose}>
            閉じる
          </button>
        </div>
        {error && <div className="form-error-banner">{error}</div>}
        <div className="form-grid">
          <Select
            label="購入制限"
            value={form.purchase_restriction || "unknown"}
            onChange={(v) => field("purchase_restriction", v)}
            options={[
              "normal",
              "pre_order",
              "personalized",
              "made_to_order",
              "client_advisor_only",
              "boutique_only",
              "research_only",
              "unknown",
            ].map((x) => [x, displayLabel(x)])}
          />
          <Select
            label="ブランド"
            value={form.brand_id}
            onChange={(v) => field("brand_id", v)}
            options={brands.map((b) => [b.id, b.brand_name])}
          />
          <Select
            label="カテゴリ"
            value={form.category_id || ""}
            onChange={(v) => field("category_id", v || null)}
            options={categories.map((c) => [c.id, c.category_name])}
          />
          <Select
            label="仕入先"
            value={form.supplier_id}
            onChange={(v) => field("supplier_id", v)}
            options={suppliers.map((s) => [s.id, s.name])}
          />
          <Input
            label="商品URL"
            value={form.supplier_product_url}
            onChange={(v) => field("supplier_product_url", v)}
          />
          <Input
            label="Product Code"
            value={form.supplier_product_code || ""}
            onChange={(v) => field("supplier_product_code", v || null)}
          />
          <Input
            label="商品名"
            value={form.product_name}
            onChange={(v) => field("product_name", v)}
          />
          <Input
            label="仕入価格"
            type="number"
            value={form.supplier_price}
            onChange={(v) => field("supplier_price", v)}
          />
          <Select
            label="通貨"
            value={form.supplier_currency}
            onChange={(v) => field("supplier_currency", v)}
            options={["EUR", "JPY", "GBP", "CHF", "USD"].map((x) => [x, x])}
          />
          <Select
            label="VATポリシー"
            value={form.vat_policy}
            onChange={(v) => field("vat_policy", v)}
            options={[
              "unknown",
              "included",
              "excluded_for_export",
              "not_refunded",
            ].map((x) => [x, displayLabel(x)])}
          />
          {form.vat_policy === "excluded_for_export" && (
            <Input
              label="VAT率（例: 0.20）"
              type="number"
              value={form.vat_rate || ""}
              onChange={(v) => field("vat_rate", v || null)}
            />
          )}
          <Input
            label="為替レート"
            type="number"
            value={form.exchange_rate}
            onChange={(v) => field("exchange_rate", v)}
          />
          <Input
            label="日本向け送料"
            type="number"
            value={form.japan_shipping_cost}
            onChange={(v) => field("japan_shipping_cost", v)}
          />
          <Input
            label="輸入費用見込"
            type="number"
            value={form.estimated_import_cost}
            onChange={(v) => field("estimated_import_cost", v)}
          />
          <Input
            label="その他費用見込"
            type="number"
            value={form.estimated_other_cost}
            onChange={(v) => field("estimated_other_cost", v)}
          />
          <Input
            label="BUYMA販売価格"
            type="number"
            value={form.buyma_price}
            onChange={(v) => field("buyma_price", v)}
          />
          <Input
            label="BUYMA手数料率"
            type="number"
            value={form.buyma_fee_rate}
            onChange={(v) => field("buyma_fee_rate", v)}
          />
          <Select
            label="在庫状況"
            value={form.availability_status}
            onChange={(v) => field("availability_status", v)}
            options={["unknown", "in_stock", "out_of_stock", "preorder"].map(
              (x) => [x, displayLabel(x)],
            )}
          />
          <Select
            label="調査ステータス"
            value={form.research_status}
            onChange={(v) => field("research_status", v)}
            options={[
              "discovered",
              "reviewing",
              "profitable",
              "unprofitable",
              "rejected",
              "ready_for_listing",
            ].map((x) => [x, displayLabel(x)])}
          />
        </div>
        {resolved && (
          <div className="panel">
            <strong>
              オンライン購入ポリシー: {displayLabel(resolved.policy)}
            </strong>
            <p className="subtle">
              適用元:{" "}
              {resolved.source === "category_override"
                ? "カテゴリ別設定"
                : "ブランド既定値"}
            </p>
          </div>
        )}
        {form.vat_policy === "unknown" && (
          <div className="vat-notice">
            VATポリシーが未確認のため、VAT控除は利益計算に適用されません。
          </div>
        )}
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={form.online_purchase_available}
            onChange={(e) =>
              field("online_purchase_available", e.target.checked)
            }
          />
          オンライン購入可能
        </label>
        <div className="row-actions">
          <button
            type="button"
            disabled={busy}
            className="secondary-button"
            onClick={() => void calculate()}
          >
            利益を計算
          </button>
          <button disabled={busy} className="primary-button">
            {candidate ? "変更を保存" : "候補を保存"}
          </button>
        </div>
        {preview && (
          <section className="price-preview" aria-label="利益プレビュー">
            <h3>利益プレビュー</h3>
            <div className="status-grid">
              <Metric
                label="実効仕入価格"
                value={money(
                  preview.effective_supplier_price,
                  form.supplier_currency,
                )}
              />
              <Metric
                label="輸出価格"
                value={money(preview.export_price, form.supplier_currency)}
              />
              <Metric
                label="仕入原価"
                value={money(preview.supplier_cost_jpy)}
              />
              <Metric label="BUYMA手数料" value={money(preview.buyma_fee)} />
              <Metric label="総費用" value={money(preview.total_cost)} />
              <Metric
                label="利益"
                value={`${money(preview.profit_amount)} (${percent(preview.profit_rate)})`}
              />
            </div>
          </section>
        )}
      </form>
    </div>
  );
}
function Input({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <label className="form-field">
      <span className="form-field__label">{label}</span>
      <input
        type={type}
        step={type === "number" ? "any" : undefined}
        className="form-field__input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[][];
}) {
  return (
    <label className="form-field">
      <span className="form-field__label">{label}</span>
      <select
        className="form-field__input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">選択してください</option>
        {options.map(([v, t]) => (
          <option key={v} value={v}>
            {t}
          </option>
        ))}
      </select>
    </label>
  );
}
function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="status-card">
      <div className="status-card__label">{label}</div>
      <div className="price-preview__value">{value}</div>
    </div>
  );
}
