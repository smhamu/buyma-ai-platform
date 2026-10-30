import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge } from "../components/ui/Badge";
import { Pagination } from "../components/ui/Pagination";
import { fetchBrands } from "../modules/brands/api";
import type { Brand } from "../modules/brands/types";
import { fetchProductCategories } from "../modules/product-categories/api";
import type { ProductCategory } from "../modules/product-categories/types";
import { label } from "../modules/product-research/format";
import {
  createCandidateFromSource,
  deleteResearchSource,
  fetchResearchSources,
  importResearchCsv,
  registerResearchUrl,
} from "../modules/research-ingestion/api";
import type {
  CsvImportResult,
  ResearchSourcePage,
} from "../modules/research-ingestion/types";
import { fetchSuppliers } from "../modules/suppliers/api";
import type { Supplier } from "../modules/suppliers/types";

export function ResearchIngestionPage() {
  const [sp, setSp] = useSearchParams();
  const [data, setData] = useState<ResearchSourcePage | null>(null);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [urlOpen, setUrlOpen] = useState(false);
  const [csvOpen, setCsvOpen] = useState(false);
  const [convertId, setConvertId] = useState<string | null>(null);
  const query = useMemo(() => {
    const p = new URLSearchParams(sp);
    if (!p.has("page")) p.set("page", "1");
    if (!p.has("page_size")) p.set("page_size", "20");
    return p.toString();
  }, [sp]);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, b, r] = await Promise.all([
        fetchSuppliers({ page_size: 100, is_active: undefined }),
        fetchBrands({ page_size: 100, is_active: undefined }),
        fetchResearchSources(query),
      ]);
      setSuppliers(s.items);
      setBrands(b.items);
      setData(r);
      setError("");
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "リサーチ元データを読み込めませんでした。",
      );
    } finally {
      setLoading(false);
    }
  }, [query]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    void fetchProductCategories().then(setCategories).catch(() => setCategories([]));
  }, []);
  const change = (key: string, value: string) => {
    const n = new URLSearchParams(sp);
    value ? n.set(key, value) : n.delete(key);
    if (key !== "page") n.set("page", "1");
    setSp(n);
  };
  const supplierName = (id: string) =>
    suppliers.find((x) => x.id === id)?.name || "不明";
  const brandName = (id: string | null) =>
    brands.find((x) => x.id === id)?.brand_name || "未照合";
  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <h1>リサーチ取込</h1>
          <p>
            外部サイトへ自動アクセスせず、商品情報の根拠を登録します。
          </p>
        </div>
        <div className="row-actions">
          <button className="secondary-button" onClick={() => setCsvOpen(true)}>
            CSV取込
          </button>
          <button className="primary-button" onClick={() => setUrlOpen(true)}>
            URLを追加
          </button>
        </div>
      </div>
      <div className="panel research-toolbar">
        <input
          aria-label="取込データを検索"
          className="form-field__input"
          value={sp.get("q") || ""}
          onChange={(e) => change("q", e.target.value)}
          placeholder="商品名、ID、URL"
        />
        <select
          aria-label="取込種別"
          className="form-field__input"
          value={sp.get("source_type") || ""}
          onChange={(e) => change("source_type", e.target.value)}
        >
          <option value="">すべての取込種別</option>
          {[
            "url_manual",
            "csv",
            "official_api",
            "structured_data",
            "html_parser",
          ].map((x) => (
            <option key={x} value={x}>{label(x)}</option>
          ))}
        </select>
        <select
          aria-label="処理ステータス"
          className="form-field__input"
          value={sp.get("processing_status") || ""}
          onChange={(e) => change("processing_status", e.target.value)}
        >
          <option value="">すべてのステータス</option>
          {[
            "pending",
            "fetched",
            "normalized",
            "matched",
            "candidate_created",
            "rejected",
            "failed",
          ].map((x) => (
            <option key={x} value={x}>{label(x)}</option>
          ))}
        </select>
      </div>
      {error && <div className="form-error-banner">{error}</div>}
      {loading ? (
        <div className="page-status">リサーチ元データを読み込み中...</div>
      ) : !data?.items.length ? (
        <div className="panel panel--empty">
          <h2>取込済みの商品はありません</h2><p>URLを登録するか、CSVファイルを取り込んでください。</p>
        </div>
      ) : (
        <div className="panel">
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>取込元</th><th>仕入先</th><th>ブランド</th><th>商品</th><th>価格</th><th>ステータス</th><th>購入制限</th><th>候補</th><th>作成日時</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((x) => (
                  <tr key={x.id}>
                    <td>
                      <a
                        className="text-link"
                        href={x.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {x.source_type}
                      </a>
                    </td>
                    <td>{supplierName(x.supplier_id)}</td>
                    <td>{brandName(x.brand_id)}</td>
                    <td>
                      {x.normalized_title ||
                        x.raw_title ||
                        "手動入力待ち"}
                    </td>
                    <td>
                      {x.normalized_price
                        ? `${x.normalized_currency} ${x.normalized_price}`
                        : "-"}
                    </td>
                    <td>
                      <Badge>{x.processing_status}</Badge>
                    </td>
                    <td><Badge>{(x.purchase_restriction || "unknown").replace(/_/g, " ")}</Badge></td>
                    <td>
                      {x.candidate_id ? (
                        <Link
                          className="text-link"
                          to={`/product-research/${x.candidate_id}`}
                        >
                          候補を開く
                        </Link>
                      ) : (
                        "未作成"
                      )}
                    </td>
                    <td>{new Date(x.created_at).toLocaleDateString()}</td>
                    <td>
                      <div className="row-actions">
                        {!x.candidate_id &&
                          x.processing_status === "matched" && (
                            <button
                              className="secondary-button"
                              onClick={() => setConvertId(x.id)}
                            >
                              候補を作成
                            </button>
                          )}
                        <button
                          className="secondary-button"
                          onClick={async () => {
                            if (window.confirm("この取込データを削除しますか？")) {
                              try {
                                await deleteResearchSource(x.id);
                                await load();
                              } catch (deleteError) {
                                setError(
                                  deleteError instanceof Error
                                    ? deleteError.message
                                    : "削除できませんでした。",
                                );
                              }
                            }
                          }}
                        >
                          削除
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={data}
            onPage={(p) => change("page", String(p))}
            onPageSize={(p) => change("page_size", String(p))}
          />
        </div>
      )}
      {urlOpen && (
        <UrlForm
          suppliers={suppliers}
          categories={categories}
          onClose={() => setUrlOpen(false)}
          onSaved={load}
        />
      )}{" "}
      {csvOpen && <CsvForm onClose={() => setCsvOpen(false)} onSaved={load} />}{" "}
      {convertId && (
        <ConvertForm
          id={convertId}
          onClose={() => setConvertId(null)}
          onSaved={load}
        />
      )}
    </section>
  );
}

function UrlForm({
  suppliers,
  categories,
  onClose,
  onSaved,
}: {
  suppliers: Supplier[];
  categories: ProductCategory[];
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [supplier, setSupplier] = useState("");
  const [url, setUrl] = useState("");
  const [category, setCategory] = useState("");
  const [restriction, setRestriction] = useState("unknown");
  const [error, setError] = useState("");
  const selected = suppliers.find((x) => x.id === supplier);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await (category
        ? registerResearchUrl(supplier, url, category, restriction)
        : registerResearchUrl(supplier, url, null, restriction));
      await onSaved();
      onClose();
    } catch (x) {
      setError(x instanceof Error ? x.message : "登録できませんでした。");
    }
  };
  return (
    <div className="modal-backdrop">
      <form
        className="modal-panel research-form"
        aria-label="URL登録フォーム"
        onSubmit={(e) => void submit(e)}
      >
        <div className="modal-panel__header">
          <h2>商品URLを追加</h2>
          <button type="button" className="secondary-button" onClick={onClose}>
            閉じる
          </button>
        </div>
        {error && <div className="form-error-banner">{error}</div>}
        <label className="form-field">
          仕入先
          <select
            className="form-field__input"
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
            required
          >
            <option value="">選択してください</option>
            {suppliers.map((x) => (
              <option key={x.id} value={x.id}>
                {x.name}
              </option>
            ))}
          </select>
        </label>
        <label className="form-field">
          カテゴリ（任意）
          <select className="form-field__input" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">カテゴリ未設定</option>
            {categories.map((x) => <option key={x.id} value={x.id}>{x.category_name}</option>)}
          </select>
        </label>
        {selected && (
          <div className="panel">
            <strong>取得ポリシー</strong>
            <p>
              {label(selected.ingestion_source_type)} · 自動取得: {selected.automated_fetch_enabled ? "有効" : "無効"}
            </p>
          </div>
        )}
        <label className="form-field">
          商品URL
          <input
            type="url"
            className="form-field__input"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
        </label>
        <label className="form-field">
          購入制限（任意）
          <select className="form-field__input" value={restriction} onChange={(e) => setRestriction(e.target.value)}>
            {["unknown", "normal", "pre_order", "personalized", "made_to_order", "client_advisor_only", "boutique_only", "research_only"].map((value) => <option key={value} value={value}>{value.replace(/_/g, " ")}</option>)}
          </select>
        </label>
        <p className="subtle">
          手動URL登録のみを行います。この操作では外部サイトを自動取得しません。
          website.
        </p>
        <button className="primary-button">URLを登録</button>
      </form>
    </div>
  );
}
function CsvForm({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<CsvImportResult | null>(null);
  const [error, setError] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    try {
      setResult(await importResearchCsv(file));
      await onSaved();
    } catch (x) {
      setError(x instanceof Error ? x.message : "取込に失敗しました。");
    }
  };
  return (
    <div className="modal-backdrop">
      <form
        className="modal-panel research-form"
        aria-label="CSV取込フォーム"
        onSubmit={(e) => void submit(e)}
      >
        <div className="modal-panel__header">
          <h2>CSV取込</h2>
          <button type="button" className="secondary-button" onClick={onClose}>
            閉じる
          </button>
        </div>
        <p>
          必須列: supplier, brand, product_url, product_name,
          supplier_product_code, supplier_price, currency, availability,
          buyma_price, category_code（任意）, purchase_restriction（任意）
        </p>
        {error && <div className="form-error-banner">{error}</div>}
        <input
          aria-label="CSVファイル"
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          required
        />
        <button className="primary-button">CSVを取り込む</button>
        {result && (
          <div className="panel">
            <strong>
              成功 {result.success_count}件 · 失敗 {result.failed_count}件 · 重複 {result.duplicate_count}件
            </strong>
            <ul>
              {result.rows.map((x) => (
                <li key={x.row}>
                  行 {x.row}: {label(x.status)}
                  {x.message ? ` - ${x.message}` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}
      </form>
    </div>
  );
}
function ConvertForm({
  id,
  onClose,
  onSaved,
}: {
  id: string;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [rate, setRate] = useState("");
  const [price, setPrice] = useState("");
  const [error, setError] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await createCandidateFromSource(id, {
        exchange_rate: rate,
        buyma_price: price,
        buyma_fee_rate: "0.077",
      });
      await onSaved();
      onClose();
    } catch (x) {
      setError(x instanceof Error ? x.message : "候補を作成できませんでした。");
    }
  };
  return (
    <div className="modal-backdrop">
      <form
        className="modal-panel research-form"
          aria-label="商品リサーチ候補変換フォーム"
        onSubmit={(e) => void submit(e)}
      >
        <div className="modal-panel__header">
          <h2>商品リサーチ候補を作成</h2>
          <button type="button" className="secondary-button" onClick={onClose}>
            閉じる
          </button>
        </div>
        {error && <div className="form-error-banner">{error}</div>}
        <label className="form-field">
          為替レート
          <input
            type="number"
            step="any"
            className="form-field__input"
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            required
          />
        </label>
        <label className="form-field">
          BUYMA販売価格
          <input
            type="number"
            step="any"
            className="form-field__input"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            required
          />
        </label>
        <button className="primary-button">候補を作成</button>
      </form>
    </div>
  );
}
