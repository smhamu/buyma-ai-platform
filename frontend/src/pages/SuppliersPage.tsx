import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { Badge } from "../components/ui/Badge";
import { Pagination } from "../components/ui/Pagination";
import { ApiClientError } from "../lib/api";
import { fetchBrands } from "../modules/brands/api";
import type { Brand } from "../modules/brands/types";
import { label } from "../modules/product-research/format";
import {
  createSupplier,
  deleteSupplier,
  fetchSuppliers,
  updateSupplier,
} from "../modules/suppliers/api";
import type {
  Supplier,
  SupplierInput,
  SupplierPage,
} from "../modules/suppliers/types";
import { SupplierPolicyEvidencePanel } from "../components/suppliers/SupplierPolicyEvidencePanel";

const blank: SupplierInput = {
  name: "",
  country_code: "FR",
  website_url: "",
  supplier_type: "unknown",
  default_currency: "EUR",
  brand_ids: [],
  ships_to_japan: false,
  vat_policy: "unknown",
  vat_rate: null,
  japan_shipping_cost: null,
  buyma_allowed_status: "unchecked",
  buyma_status_checked_at: null,
  research_status: "discovered",
  notes: null,
  is_active: true,
  ingestion_source_type: "manual",
  automated_fetch_enabled: false,
  terms_status: "unchecked",
  robots_status: "unchecked",
  terms_checked_at: null,
  robots_checked_at: null,
  official_api_available: false,
  research_policy_notes: null,
  parser_key: null,
  request_interval_seconds: null,
  last_fetch_at: null,
};
export function SuppliersPage() {
  const [sp, setSp] = useSearchParams();
  const [data, setData] = useState<SupplierPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Supplier | null | undefined>();
  const [evidenceSupplier, setEvidenceSupplier] = useState<Supplier | null>(null);
  const query = useMemo(
    () => ({
      country: sp.get("country") || undefined,
      supplier_type: sp.get("type") || undefined,
      ships_to_japan: sp.has("ships") ? sp.get("ships") === "true" : undefined,
      buyma_allowed_status: sp.get("buyma") || undefined,
      is_active: sp.has("active") ? sp.get("active") === "true" : undefined,
      page: Number(sp.get("page") || 1),
      page_size: Number(sp.get("page_size") || 20),
      sort_by: (sp.get("sort") || "created_at") as "created_at",
      sort_order: "desc" as const,
    }),
    [sp],
  );
  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchSuppliers(query));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load suppliers.");
    } finally {
      setLoading(false);
    }
  }, [query]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    const evidenceId = sp.get("evidence");
    const focusId = sp.get("focus");
    const supplier = data?.items.find((item) => item.id === (evidenceId || focusId));
    if (supplier && evidenceId) setEvidenceSupplier(supplier);
    if (supplier && focusId) setEditing(supplier);
  }, [data, sp]);
  const change = (k: string, v: string) => {
    const n = new URLSearchParams(sp);
    v ? n.set(k, v) : n.delete(k);
    if (k !== "page") n.set("page", "1");
    setSp(n);
  };
  const remove = async (s: Supplier) => {
    if (!window.confirm(`Delete ${s.name}?`)) return;
    try {
      await deleteSupplier(s.id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed.");
    }
  };
  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <h1>Suppliers</h1>
          <p>EU stores, shipping, VAT, and BUYMA purchasing status.</p>
        </div>
        <button className="primary-button" onClick={() => setEditing(null)}>
          Add Supplier
        </button>
      </div>
      <div className="panel research-toolbar">
        <select
          aria-label="Country"
          className="form-field__input"
          value={sp.get("country") || ""}
          onChange={(e) => change("country", e.target.value)}
        >
          <option value="">All countries</option>
          {["FR", "IT", "DE", "ES", "NL", "BE", "AT", "IE", "PT"].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
        <select
          aria-label="Supplier type"
          className="form-field__input"
          value={sp.get("type") || ""}
          onChange={(e) => change("type", e.target.value)}
        >
          <option value="">All types</option>
          {[
            "authorized_retailer",
            "department_store",
            "boutique",
            "marketplace",
            "other",
            "unknown",
          ].map((x) => (
            <option key={x} value={x}>
              {label(x)}
            </option>
          ))}
        </select>
        <select
          aria-label="Ships to Japan"
          className="form-field__input"
          value={sp.get("ships") || ""}
          onChange={(e) => change("ships", e.target.value)}
        >
          <option value="">Any shipping</option>
          <option value="true">Ships to Japan</option>
          <option value="false">Does not ship</option>
        </select>
        <select
          aria-label="BUYMA status"
          className="form-field__input"
          value={sp.get("buyma") || ""}
          onChange={(e) => change("buyma", e.target.value)}
        >
          <option value="">All BUYMA statuses</option>
          {["unchecked", "allowed", "caution", "prohibited"].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
      </div>
      {error && <div className="form-error-banner">{error}</div>}
      {loading ? (
        <div className="page-status">Loading suppliers...</div>
      ) : !data?.items.length ? (
        <div className="panel panel--empty">
          <h2>No suppliers found.</h2>
        </div>
      ) : (
        <div className="panel">
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Supplier</th>
                  <th>Country</th>
                  <th>Brands</th>
                  <th>Shipping</th>
                  <th>VAT</th>
                  <th>BUYMA</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <strong>{s.name}</strong>
                      <div className="subtle">
                        {label(s.supplier_type)} · {s.default_currency}
                      </div>
                    </td>
                    <td>{s.country_code}</td>
                    <td>
                      <div className="chip-list">
                        {s.brands.slice(0, 2).map((b) => (
                          <Badge key={b.id}>{b.brand_name}</Badge>
                        ))}
                        {s.brands.length > 2 && (
                          <Badge tone="muted">+{s.brands.length - 2}</Badge>
                        )}
                      </div>
                    </td>
                    <td>
                      {s.ships_to_japan
                        ? "Ships to Japan"
                        : "No Japan shipping"}
                    </td>
                    <td>{label(s.vat_policy)}</td>
                    <td>
                      <Badge
                        tone={
                          s.buyma_allowed_status === "prohibited"
                            ? "danger"
                            : s.buyma_allowed_status === "allowed"
                              ? "success"
                              : "warning"
                        }
                      >
                        {label(s.buyma_allowed_status)}
                      </Badge>
                    </td>
                    <td>
                      <div className="row-actions">
                        <a
                          className="text-link"
                          href={s.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Website
                        </a>
                        <button
                          className="secondary-button"
                          onClick={() => setEvidenceSupplier(s)}
                        >
                          Policy Evidence
                        </button>
                        <button
                          className="secondary-button"
                          onClick={() => setEditing(s)}
                        >
                          Edit
                        </button>
                        <button
                          className="secondary-button"
                          onClick={() => void remove(s)}
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
            onPageSize={(s) => change("page_size", String(s))}
          />
        </div>
      )}
      {editing !== undefined && (
        <SupplierForm
          supplier={editing}
          onClose={() => setEditing(undefined)}
          onSaved={() => {
            setEditing(undefined);
            void load();
          }}
        />
      )}
      {evidenceSupplier && <SupplierPolicyEvidencePanel supplier={evidenceSupplier} onClose={() => setEvidenceSupplier(null)} />}
    </section>
  );
}
function SupplierForm({
  supplier,
  onClose,
  onSaved,
}: {
  supplier: Supplier | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [form, setForm] = useState<SupplierInput>(
    supplier
      ? { ...supplier, brand_ids: supplier.brands.map((b) => b.id) }
      : blank,
  );
  const [error, setError] = useState("");
  useEffect(() => {
    void fetchBrands({ page_size: 100, is_active: undefined })
      .then((x) => setBrands(x.items))
      .catch(() => setError("Failed to load brands."));
  }, []);
  const field = (key: keyof SupplierInput, value: unknown) =>
    setForm({ ...form, [key]: value });
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.website_url) {
      setError("Name and website URL are required.");
      return;
    }
    try {
      supplier
        ? await updateSupplier(supplier.id, form)
        : await createSupplier(form);
      onSaved();
    } catch (x) {
      setError(x instanceof ApiClientError ? x.message : "Save failed.");
    }
  };
  return (
    <div className="modal-backdrop">
      <form
        className="modal-panel research-form"
        onSubmit={(e) => void submit(e)}
      >
        <div className="modal-panel__header">
          <h2>{supplier ? "Edit Supplier" : "Add Supplier"}</h2>
          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
        {error && <div className="form-error-banner">{error}</div>}
        <label className="form-field">
          Name
          <input
            className="form-field__input"
            value={form.name}
            onChange={(e) => field("name", e.target.value)}
          />
        </label>
        <label className="form-field">
          Website URL
          <input
            className="form-field__input"
            value={form.website_url}
            onChange={(e) => field("website_url", e.target.value)}
          />
        </label>
        <div className="form-grid">
          <label className="form-field">
            Country
            <select
              className="form-field__input"
              value={form.country_code}
              onChange={(e) => field("country_code", e.target.value)}
            >
              {["FR", "IT", "DE", "ES", "NL", "BE", "AT", "IE", "PT"].map(
                (x) => (
                  <option key={x}>{x}</option>
                ),
              )}
            </select>
          </label>
          <label className="form-field">
            Type
            <select
              className="form-field__input"
              value={form.supplier_type}
              onChange={(e) => field("supplier_type", e.target.value)}
            >
              {[
                "authorized_retailer",
                "department_store",
                "boutique",
                "marketplace",
                "other",
                "unknown",
              ].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Currency
            <select
              className="form-field__input"
              value={form.default_currency}
              onChange={(e) => field("default_currency", e.target.value)}
            >
              {["EUR", "JPY", "GBP", "CHF", "USD"].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            VAT policy
            <select
              className="form-field__input"
              value={form.vat_policy}
              onChange={(e) => field("vat_policy", e.target.value)}
            >
              {[
                "unknown",
                "included",
                "excluded_for_export",
                "not_refunded",
              ].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            VAT rate
            <input
              type="number"
              step="0.01"
              className="form-field__input"
              value={form.vat_rate || ""}
              onChange={(e) => field("vat_rate", e.target.value || null)}
            />
          </label>
          <label className="form-field">
            Japan shipping cost
            <input
              type="number"
              className="form-field__input"
              value={form.japan_shipping_cost || ""}
              onChange={(e) =>
                field("japan_shipping_cost", e.target.value || null)
              }
            />
          </label>
          <label className="form-field">
            BUYMA status
            <select
              className="form-field__input"
              value={form.buyma_allowed_status}
              onChange={(e) => field("buyma_allowed_status", e.target.value)}
            >
              {["unchecked", "allowed", "caution", "prohibited"].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Research status
            <select
              className="form-field__input"
              value={form.research_status}
              onChange={(e) => field("research_status", e.target.value)}
            >
              {["discovered", "reviewing", "approved", "rejected"].map((x) => (
                <option key={x}>{x}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            Ingestion source
            <select className="form-field__input" value={form.ingestion_source_type} onChange={(e)=>field("ingestion_source_type",e.target.value)}>
              {["manual","url_manual","csv","official_api","structured_data","html_parser","disabled"].map((x)=><option key={x}>{x}</option>)}
            </select>
          </label>
          <label className="form-field">
            Terms status
            <select className="form-field__input" value={form.terms_status} onChange={(e)=>field("terms_status",e.target.value)}>
              {["unchecked","allowed","restricted","prohibited","unknown"].map((x)=><option key={x}>{x}</option>)}
            </select>
          </label>
          <label className="form-field">
            Robots status
            <select className="form-field__input" value={form.robots_status} onChange={(e)=>field("robots_status",e.target.value)}>
              {["unchecked","allowed","restricted","disallowed","unknown"].map((x)=><option key={x}>{x}</option>)}
            </select>
          </label>
        </div>
        <fieldset className="brand-picker">
          <legend>Brands</legend>
          {brands.map((b) => (
            <label className="checkbox-field" key={b.id}>
              <input
                type="checkbox"
                checked={form.brand_ids.includes(b.id)}
                onChange={(e) =>
                  field(
                    "brand_ids",
                    e.target.checked
                      ? [...form.brand_ids, b.id]
                      : form.brand_ids.filter((x) => x !== b.id),
                  )
                }
              />
              {b.brand_name}
              {!b.is_active || !b.is_research_enabled
                ? " (inactive/research disabled)"
                : ""}
            </label>
          ))}
        </fieldset>
        <label className="checkbox-field">
          <input type="checkbox" checked={form.automated_fetch_enabled} onChange={(e)=>field("automated_fetch_enabled",e.target.checked)}/>
          Automated fetch enabled
        </label>
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={form.ships_to_japan}
            onChange={(e) => field("ships_to_japan", e.target.checked)}
          />
          Ships to Japan
        </label>
        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => field("is_active", e.target.checked)}
          />
          Active
        </label>
        <label className="form-field">
          Notes
          <textarea
            className="form-field__input"
            value={form.notes || ""}
            onChange={(e) => field("notes", e.target.value || null)}
          />
        </label>
        <button className="primary-button">Save Supplier</button>
      </form>
    </div>
  );
}
