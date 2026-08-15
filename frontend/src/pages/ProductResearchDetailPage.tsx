import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { CandidateForm } from "../components/research/CandidateForm";
import { Badge } from "../components/ui/Badge";
import { ApiClientError } from "../lib/api";
import { fetchBrand } from "../modules/brands/api";
import type { Brand } from "../modules/brands/types";
import { fetchCandidate } from "../modules/product-research/api";
import { label, money, percent } from "../modules/product-research/format";
import type { Candidate } from "../modules/product-research/types";
import { fetchSupplier } from "../modules/suppliers/api";
import type { Supplier } from "../modules/suppliers/types";

export function ProductResearchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [c, setC] = useState<Candidate | null>(null);
  const [b, setB] = useState<Brand | null>(null);
  const [s, setS] = useState<Supplier | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [edit, setEdit] = useState(false);
  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const candidate = await fetchCandidate(id);
      const [brand, supplier] = await Promise.all([
        fetchBrand(candidate.brand_id),
        fetchSupplier(candidate.supplier_id),
      ]);
      setC(candidate);
      setB(brand);
      setS(supplier);
    } catch (e) {
      setError(
        e instanceof ApiClientError && e.status === 404
          ? "Research candidate not found."
          : e instanceof Error
            ? e.message
            : "Failed to load candidate.",
      );
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => {
    void load();
  }, [load]);
  if (loading)
    return <div className="page-status">Loading research candidate...</div>;
  if (error || !c)
    return (
      <div className="panel panel--error">
        <h1>Unable to load candidate</h1>
        <p>{error}</p>
      </div>
    );
  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <Link className="text-link" to="/product-research">
            ← Research Candidates
          </Link>
          <h1>{c.product_name}</h1>
          <p>{b?.brand_name}</p>
        </div>
        <button className="primary-button" onClick={() => setEdit(true)}>
          Edit Candidate
        </button>
      </div>
      <div className="detail-grid">
        <Section title="Overview">
          <Row k="Brand" v={b?.brand_name} />
          <Row k="Product" v={c.product_name} />
          <Row k="Supplier" v={s?.name} />
          <Row k="Availability" v={label(c.availability_status)} />
          <Row
            k="Purchase restriction"
            v={<Badge tone={c.purchase_restriction === "normal" ? "success" : "neutral"}>{label(c.purchase_restriction || "unknown")}</Badge>}
          />
          <Row
            k="Product URL"
            v={
              <a
                className="text-link"
                href={c.supplier_product_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open supplier product
              </a>
            }
          />
        </Section>
        <Section title="Purchase Cost">
          <Row
            k="Supplier price"
            v={money(c.supplier_price, c.supplier_currency)}
          />
          <Row k="VAT policy" v={label(c.vat_policy)} />
          <Row
            k="Export price"
            v={money(c.export_price, c.supplier_currency)}
          />
          <Row k="Exchange rate" v={c.exchange_rate} />
          <Row k="Supplier cost" v={money(c.supplier_cost_jpy)} />
          <Row k="Shipping" v={money(c.japan_shipping_cost)} />
          <Row k="Import cost" v={money(c.estimated_import_cost)} />
          <Row k="Other cost" v={money(c.estimated_other_cost)} />
        </Section>
        <Section title="BUYMA">
          <Row k="BUYMA price" v={money(c.buyma_price)} />
          <Row k="BUYMA fee" v={money(c.buyma_fee)} />
          <Row
            k="Supplier status"
            v={
              <Badge
                tone={
                  s?.buyma_allowed_status === "prohibited"
                    ? "danger"
                    : "neutral"
                }
              >
                {label(s?.buyma_allowed_status || "unknown")}
              </Badge>
            }
          />
        </Section>
        <Section title="Profit">
          <Row k="Total cost" v={money(c.total_cost)} />
          <Row
            k="Profit amount"
            v={`${Number(c.profit_amount) >= 0 ? "+" : ""}${money(c.profit_amount)}`}
          />
          <Row k="Profit rate" v={percent(c.profit_rate)} />
        </Section>
        <Section title="Research">
          <Row k="Status" v={label(c.research_status)} />
          <Row
            k="Checked"
            v={
              c.checked_at
                ? new Date(c.checked_at).toLocaleString()
                : "Not checked"
            }
          />
          <Row
            k="Online purchase"
            v={c.online_purchase_available ? "Available" : "Unavailable"}
          />
          {c.vat_policy === "unknown" && (
            <Row k="VAT note" v="VAT deduction is not assumed." />
          )}
        </Section>
      </div>
      {edit && (
        <CandidateForm
          candidate={c}
          onClose={() => setEdit(false)}
          onSaved={() => void load()}
        />
      )}
    </section>
  );
}
function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      <div className="detail-list">{children}</div>
    </section>
  );
}
function Row({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div className="detail-row">
      <div className="detail-row__label">{k}</div>
      <div className="detail-row__value">{v || "-"}</div>
    </div>
  );
}
