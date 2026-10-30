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
          ? "商品リサーチ候補が見つかりません。"
          : e instanceof Error
            ? e.message
            : "商品リサーチ候補を読み込めませんでした。",
      );
    } finally {
      setLoading(false);
    }
  }, [id]);
  useEffect(() => {
    void load();
  }, [load]);
  if (loading)
    return <div className="page-status">商品リサーチ候補を読み込み中...</div>;
  if (error || !c)
    return (
      <div className="panel panel--error">
        <h1>商品リサーチ候補を読み込めませんでした</h1>
        <p>{error}</p>
      </div>
    );
  return (
    <section className="page-section">
      <div className="page-section__header">
        <div>
          <Link className="text-link" to="/product-research">
            ← 商品リサーチ候補一覧
          </Link>
          <h1>{c.product_name}</h1>
          <p>{b?.brand_name}</p>
        </div>
        <button className="primary-button" onClick={() => setEdit(true)}>
          候補を編集
        </button>
      </div>
      <div className="detail-grid">
        <Section title="概要"><Row k="ブランド" v={b?.brand_name} /><Row k="商品" v={c.product_name} /><Row k="仕入先" v={s?.name} /><Row k="在庫状況" v={label(c.availability_status)} />
          <Row
            k="購入制限"
            v={<Badge tone={c.purchase_restriction === "normal" ? "success" : "neutral"}>{label(c.purchase_restriction || "unknown")}</Badge>}
          />
          <Row
            k="商品URL"
            v={
              <a
                className="text-link"
                href={c.supplier_product_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                仕入先の商品ページを開く
              </a>
            }
          />
        </Section>
        <Section title="仕入費用">
          <Row
            k="仕入価格"
            v={money(c.supplier_price, c.supplier_currency)}
          />
          <Row k="VATポリシー" v={label(c.vat_policy)} />
          <Row
            k="輸出価格"
            v={money(c.export_price, c.supplier_currency)}
          />
          <Row k="為替レート" v={c.exchange_rate} /><Row k="仕入原価" v={money(c.supplier_cost_jpy)} /><Row k="日本向け送料" v={money(c.japan_shipping_cost)} /><Row k="輸入費用" v={money(c.estimated_import_cost)} /><Row k="その他費用" v={money(c.estimated_other_cost)} />
        </Section>
        <Section title="BUYMA">
          <Row k="BUYMA販売価格" v={money(c.buyma_price)} /><Row k="BUYMA手数料" v={money(c.buyma_fee)} />
          <Row
            k="仕入先ステータス"
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
        <Section title="利益"><Row k="総費用" v={money(c.total_cost)} />
          <Row
            k="利益額"
            v={`${Number(c.profit_amount) >= 0 ? "+" : ""}${money(c.profit_amount)}`}
          />
          <Row k="利益率" v={percent(c.profit_rate)} />
        </Section>
        <Section title="調査"><Row k="ステータス" v={label(c.research_status)} />
          <Row
            k="確認日時"
            v={
              c.checked_at
                ? new Date(c.checked_at).toLocaleString("ja-JP")
                : "未確認"
            }
          />
          <Row
            k="オンライン購入"
            v={c.online_purchase_available ? "購入可能" : "購入不可"}
          />
          {c.vat_policy === "unknown" && (
            <Row k="VAT注記" v="VAT控除は利益計算に適用されていません。" />
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
