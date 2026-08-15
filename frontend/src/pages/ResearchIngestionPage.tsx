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
        e instanceof Error ? e.message : "Failed to load research sources.",
      );
    } finally {
      setLoading(false);
    }
  }, [query]);
  useEffect(() => {
    void load();
  }, [load]);
  const change = (key: string, value: string) => {
    const n = new URLSearchParams(sp);
    value ? n.set(key, value) : n.delete(key);
    if (key !== "page") n.set("page", "1");
    setSp(n);
  };
  const supplierName = (id: string) =>
    suppliers.find((x) => x.id === id)?.name || "Unknown";
  const brandName = (id: string | null) =>
    brands.find((x) => x.id === id)?.brand_name || "Unmatched";
  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <h1>Research Ingestion</h1>
          <p>
            Register external product evidence without automatically fetching
            supplier websites.
          </p>
        </div>
        <div className="row-actions">
          <button className="secondary-button" onClick={() => setCsvOpen(true)}>
            CSV Import
          </button>
          <button className="primary-button" onClick={() => setUrlOpen(true)}>
            Add URL
          </button>
        </div>
      </div>
      <div className="panel research-toolbar">
        <input
          aria-label="Search sources"
          className="form-field__input"
          value={sp.get("q") || ""}
          onChange={(e) => change("q", e.target.value)}
          placeholder="Product, ID, or URL"
        />
        <select
          aria-label="Source type"
          className="form-field__input"
          value={sp.get("source_type") || ""}
          onChange={(e) => change("source_type", e.target.value)}
        >
          <option value="">All source types</option>
          {[
            "url_manual",
            "csv",
            "official_api",
            "structured_data",
            "html_parser",
          ].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
        <select
          aria-label="Processing status"
          className="form-field__input"
          value={sp.get("processing_status") || ""}
          onChange={(e) => change("processing_status", e.target.value)}
        >
          <option value="">All statuses</option>
          {[
            "pending",
            "fetched",
            "normalized",
            "matched",
            "candidate_created",
            "rejected",
            "failed",
          ].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
      </div>
      {error && <div className="form-error-banner">{error}</div>}
      {loading ? (
        <div className="page-status">Loading research sources...</div>
      ) : !data?.items.length ? (
        <div className="panel panel--empty">
          <h2>No source products found.</h2>
          <p>Add a URL or import a CSV file to begin.</p>
        </div>
      ) : (
        <div className="panel">
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Supplier</th>
                  <th>Brand</th>
                  <th>Product</th>
                  <th>Price</th>
                  <th>Status</th>
                  <th>Candidate</th>
                  <th>Created</th>
                  <th>Actions</th>
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
                        "Pending manual entry"}
                    </td>
                    <td>
                      {x.normalized_price
                        ? `${x.normalized_currency} ${x.normalized_price}`
                        : "-"}
                    </td>
                    <td>
                      <Badge>{x.processing_status}</Badge>
                    </td>
                    <td>
                      {x.candidate_id ? (
                        <Link
                          className="text-link"
                          to={`/product-research/${x.candidate_id}`}
                        >
                          Open Candidate
                        </Link>
                      ) : (
                        "Not created"
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
                              Create Candidate
                            </button>
                          )}
                        <button
                          className="secondary-button"
                          disabled={!!x.candidate_id}
                          onClick={async () => {
                          if (window.confirm("Delete this source record?")) {
                              await deleteResearchSource(x.id);
                              await load();
                            }
                          }}
                        >
                          Delete
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
  onClose,
  onSaved,
}: {
  suppliers: Supplier[];
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [supplier, setSupplier] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const selected = suppliers.find((x) => x.id === supplier);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await registerResearchUrl(supplier, url);
      await onSaved();
      onClose();
    } catch (x) {
      setError(x instanceof Error ? x.message : "Registration failed.");
    }
  };
  return (
    <div className="modal-backdrop">
      <form
        className="modal-panel research-form"
        aria-label="URL import form"
        onSubmit={(e) => void submit(e)}
      >
        <div className="modal-panel__header">
          <h2>Add Product URL</h2>
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
        {error && <div className="form-error-banner">{error}</div>}
        <label className="form-field">
          Supplier
          <select
            className="form-field__input"
            value={supplier}
            onChange={(e) => setSupplier(e.target.value)}
            required
          >
            <option value="">Select...</option>
            {suppliers.map((x) => (
              <option key={x.id} value={x.id}>
                {x.name}
              </option>
            ))}
          </select>
        </label>
        {selected && (
          <div className="panel">
            <strong>Acquisition policy</strong>
            <p>
              {selected.ingestion_source_type} · Automated fetching{" "}
              {selected.automated_fetch_enabled ? "enabled" : "disabled"}
            </p>
          </div>
        )}
        <label className="form-field">
          Product URL
          <input
            type="url"
            className="form-field__input"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
        </label>
        <p className="subtle">
          Manual URL registration only. This action does not fetch the external
          website.
        </p>
        <button className="primary-button">Register URL</button>
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
      setError(x instanceof Error ? x.message : "Import failed.");
    }
  };
  return (
    <div className="modal-backdrop">
      <form
        className="modal-panel research-form"
        aria-label="CSV import form"
        onSubmit={(e) => void submit(e)}
      >
        <div className="modal-panel__header">
          <h2>CSV Import</h2>
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
        <p>
          Expected columns: supplier, brand, product_url, product_name,
          supplier_product_code, supplier_price, currency, availability,
          buyma_price (optional)
        </p>
        {error && <div className="form-error-banner">{error}</div>}
        <input
          aria-label="CSV file"
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          required
        />
        <button className="primary-button">Import CSV</button>
        {result && (
          <div className="panel">
            <strong>
              {result.success_count} success · {result.failed_count} failed ·{" "}
              {result.duplicate_count} duplicate
            </strong>
            <ul>
              {result.rows.map((x) => (
                <li key={x.row}>
                  Row {x.row}: {x.status}
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
      setError(x instanceof Error ? x.message : "Conversion failed.");
    }
  };
  return (
    <div className="modal-backdrop">
      <form
        className="modal-panel research-form"
        aria-label="Candidate conversion form"
        onSubmit={(e) => void submit(e)}
      >
        <div className="modal-panel__header">
          <h2>Create Candidate</h2>
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
        {error && <div className="form-error-banner">{error}</div>}
        <label className="form-field">
          Exchange rate
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
          BUYMA price
          <input
            type="number"
            step="any"
            className="form-field__input"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            required
          />
        </label>
        <button className="primary-button">Create Candidate</button>
      </form>
    </div>
  );
}
